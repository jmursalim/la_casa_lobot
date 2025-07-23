# Jordi Mursalim 2025
# Recommend a movie based on a given movie
# Data Wrangling based on TMDB Movie Dataset Analysis by Yinghao Zhang
# Text count vectorizer cosine simularity matrix based on Movie Recommendation by Mrinank Bhowmick

import numpy as np
import pandas as pd
import dotenv
import os
import csv
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler

file_sim_matrix = 'sim_matrix.csv'
file_dataset = 'sample_movie_dataset.csv'

# READ ME
# This code has 2 uses:
# The first is to create a simularity matrix and save it to csv
#   *when this file is run
#
# The second is a function to recommend a movie based on that matrix
#   *when the function is called

# CREATING SIMULARITY MATRIX

# open the movie database csv file
df = pd.read_csv(file_dataset)

# columns = ['index', 'movie_id', 'title', 'genres', 'overview', 'keywords', 'runtime', 'origin_country', 'popularity',
#           'vote_count', 'vote_average', 'production_companies', 'release_date', 'budget', 'cast', 'director']

features = ['keywords', 'cast', 'genres', 'director', 'production_companies', 'release_date', 'vote_average', 'popularity']

# preprocessing to remove unused columns
df.drop_duplicates(inplace=True)
drop_columns = ['movie_id', 'overview', 'budget', 'runtime', 'vote_count',]
df.drop(drop_columns, axis=1, inplace=True)

# preprocessing to remove empty values
for feature in features:
    df[feature] = df[feature].fillna("")

# function to create a new column to be count vectorized
def combine_features_text(row):
    return (
        row['keywords']
        + ' '
        + row['cast']
        + ' ' 
        + row['genres']
        + ' '
        + row['director']
        + ' '
        + row['production_companies']
    ).lower().strip()

# for text based data
# this segment of code gets the count vector of the words used through the data set, then makes a cosine similarity

# creates a new column in the dataframe with each of the words to be vectorized
df['combined_features_text'] = df.apply(combine_features_text, axis=1)

# creates a count vectorizer object
cv = CountVectorizer()
count_matrix = cv.fit_transform(df['combined_features_text'])

# cosine similarity matrix
sim_matrix_text = cosine_similarity(count_matrix)

# for numerical data
# this segment of code normalizes numerical data then weighs their averages, then gets another cosine similarity
# popularity will use both a log transform and a min-max scaling
# the vote_average and release_date features will only be min-max scaled,
# release_date will also be treated as a seperate similarity, as I want to tune the weighting of the 3 similarities (text, numerical, release date)

# creating scaler object
scaler = MinMaxScaler()

# creating popularity column log scaled
df['popularity_log'] = np.log(df['popularity'] + 1)

# scaling both popularity and vote_average with min-max
for column in ['popularity_log', 'vote_average']:
    df[f'{column}_scaled'] = scaler.fit_transform(df[[column]])

num_features = df[['popularity_log_scaled', 'vote_average_scaled']].values
sim_matrix_num = cosine_similarity(num_features)

# new column for the release year
df['release_year'] = pd.to_datetime(df['release_date'], errors='coerce').dt.year

# time based similarity formula that punishes if the film was made a long time from the target movie
years = df['release_year'].values
alpha = 0.05

# compute absolute differences across all pairs
year_diff_matrix = np.abs(years[:, np.newaxis] - years[np.newaxis, :])

# apply exponential decay
sim_matrix_time = np.exp(-alpha * year_diff_matrix)

# final combined similarity
# weightings of the three similarities
# Adjust these to suit your values
w_text = 0.7
w_num = 0.25
w_time = 0.5

# total simularity matrix
sim_matrix_total = (w_text * sim_matrix_text + w_num * sim_matrix_num + w_time * sim_matrix_time)

# save simularity matrix
np.savetxt(file_sim_matrix, sim_matrix_total, delimiter=',')
print('saving matrix to csv')


# RECOMMENDING A MOVIE

def recommend_movie(title, number_of_movies):
    recommendations = []
    file_sim_matrix = 'sim_matrix.csv'
    file_dataset = 'sample_movie_dataset.csv'

    # load the simularity matrix
    sim_total = np.loadtxt(file_sim_matrix, delimiter=',')
    # load the dataframe that matches movie title to index
    df = pd.read_csv(file_dataset)

    def get_title_from_index(index):
        return df[df.index == index]['title'].values[0]


    def get_index_from_title(title):
        return df[df.title == title]['index'].values[0]

    try:
        movie_index = get_index_from_title(title)
        similar_movies = list(enumerate(sim_total[movie_index]))

        # the next two lines of code set a filter on the similar movies tuple
        # any movies that are not similar enough are not added to the list to be
        # sorted, as the dataset we are working with is quite large, this reduces
        # the time complexity

        # filter movies that do not meet a certain similarity
        lowest_similarity = 0.45
        filtered_similar_movies = list(filter(lambda x: x[1] >= lowest_similarity, similar_movies))

        # sort the movies
        sorted_similar_movies = sorted(filtered_similar_movies, key=lambda x: x[1], reverse=True)[1:]

        # return the similar movies
        for i in range(number_of_movies):
            recommendations.append(get_title_from_index(sorted_similar_movies[i][0]))
        return recommendations
    
    # error handling
    except Exception as e:
        print(e)
        pass

    return recommendations

# debugging
# movie_list = recommend_movie('Tron', 7)
# print(movie_list)