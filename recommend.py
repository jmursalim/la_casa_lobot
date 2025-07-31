# Jordi Mursalim 2025
# Recommend a movie based on a given movie
# Data Wrangling based on TMDB Movie Dataset Analysis by Yinghao Zhang
# Text count vectorizer cosine simularity matrix based on Movie Recommendation by Mrinank Bhowmick

import numpy as np
from scipy.sparse import csr_matrix, save_npz, load_npz
import pandas as pd
import dotenv
import os
import csv
from sklearn.feature_extraction import text
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import string
import json

nltk.download('stopwords')
nltk.download('punkt_tab')
nltk.download('punkt')

stop_words = set(stopwords.words('english'))

file_test_sim_json = 'test_sim_matrix.json'
file_sim_matrix = 'sim_matrix.csv'
file_sim_matrix_json = 'sim_matrix.json'
file_dataset = 'movie_db.csv'

file_sim_matrix_test = 'test_sim_matrix.csv'
file_text_sim = 'text_sim_matrix.csv'
file_num_sim = 'num_sim_matrix.csv'
file_time_sim = 'time_sim_matrix.csv'

# READ ME
# This code has 2 uses:
# The first is to create a simularity matrix and save it to csv
#   *when this file is run
#
# The second is a function to recommend a movie based on that matrix
#   *when the function is called

# CREATING SIMULARITY MATRIX

def create_matrix():

# open the movie database csv file
    df = pd.read_csv(file_dataset)

# columns = ['index', 'movie_id', 'title', 'genres', 'overview', 'keywords', 'runtime', 'origin_country', 'popularity',
#           'vote_count', 'vote_average', 'production_companies', 'release_date', 'budget', 'cast', 'director']

    text_features = ['keywords', 'cast', 'genres', 'director', 'production_companies', 'origin_country', 'overview'] # words
    num_features = ['release_date', 'vote_average', 'popularity'] # numbers

# preprocessing to remove unused columns
    df.drop_duplicates(inplace=True)
    drop_columns = ['movie_id', 'budget', 'runtime', 'vote_count',]
    df.drop(drop_columns, axis=1, inplace=True)

# preprocessing to remove empty values
    for feature in text_features + num_features:
        df[feature] = df[feature].fillna("")

# processing the overview text to clean the text and remove stop words
    def remove_stop_words(overview):
        # remove punctuation
        clean_overview = overview.lower().strip().translate(str.maketrans('', '', string.punctuation))
        
        # turns into a list
        token_overview = word_tokenize(clean_overview)

        # returns a list without the stop words
        filtered_overview = [word for word in token_overview if word not in stop_words]

        # returns a string, as count vectorizer expects a string
        return ' '.join(filtered_overview)

# weightings of each of the sources of words
    word_weight = {
        'keywords': 5,
        'cast': 3,
        'genres': 4,
        'director': 4,
        'production_companies': 1,
        'origin_country': 1,
        'overview': 5
    }

# function to create a new column to be count vectorized
# this duplicates the words that appear in each input feature, to weight features independently
    def combine_features_text(row):
        combined_row = []

        #iterates through the word weight dictionary for each feature
        for feature, weight in word_weight.items():
            text = row[feature]

            # removes stop words from overview
            if feature == 'overview':
                text = remove_stop_words(row[feature])
            
            # repeat the text in the feature by the weight of the feature
            weighted_text = (text + ' ') * weight
            combined_row.append(weighted_text.strip())

        # return a string
        return ' '.join(combined_row).lower().strip()

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
    w_text = 0.8
    w_num = 0.15
    w_time = 0.05

# total simularity matrix
    sim_matrix_total = (w_text * sim_matrix_text + w_num * sim_matrix_num + w_time * sim_matrix_time)

# debugging
    # save simularity matrix to csv
    # np.savetxt(file_sim_matrix_test, sim_matrix_total, delimiter=',')
    # np.savetxt(file_text_sim, sim_matrix_text, delimiter=',')
    # np.savetxt(file_num_sim, sim_matrix_num, delimiter=',')
    # np.savetxt(file_time_sim, sim_matrix_time, delimiter=',')
    # print('saving matrix to csv')

# since the dataset will be large, we are turning it into a sparse matrix with the first 20 most similar movies saved
# row wise, since csr is row based, sort the 20 most similar entries, and then replace all others with 0
# could be done row wise by enumerating to save column index and similarity as a tuple, then sorting that list
    sorted_sim_matrix = {}
    test_sorted_sim_matrix = {}
    similarity_threshold = 0.2
    for i, row in enumerate(sim_matrix_total):
        enumerated_row = list(enumerate(row))

        # the next two lines of code set a filter on the similar movies tuple
        # any movies that are not similar enough are not added to the list to be
        # sorted, as the dataset we are working with is quite large, this reduces
        # the time complexity

        # filter movies that do not meet a certain similarity
        filtered_row = list(filter(lambda x: x[1] >= similarity_threshold, enumerated_row))

        # sort the row and leave the 20 highest entries
        sorted_row = sorted(filtered_row, key=lambda x: x[1], reverse=True)[1:21]

        sorted_sim_matrix[i] = [ cell[0] for cell in sorted_row ]

        # test_sorted_sim_matrix[i] = sorted_row

    try:
        with open(file_sim_matrix_json, mode='w', encoding='utf-8') as file_out:
            json.dump(sorted_sim_matrix, file_out)
        # with open(file_test_sim_json, mode='w', encoding='utf-8') as file_out:
            # json.dump(test_sorted_sim_matrix, file_out)
    except Exception as e:
        print(f'error occured: {e}')



# RECOMMENDING A MOVIE

def recommend_movie(title, number_of_movies):
    file_sim_json = 'sim_matrix.json'
    file_dataset = 'movie_db.csv'

    # load the simularity matrix
    with open(file_sim_json, 'r') as file:
        sim_total = json.load(file)
    # load the dataframe that matches movie title to index
    df = pd.read_csv(file_dataset)

    for feature in df:
        df[feature] = df[feature].fillna("")
    
    def get_title_from_index(index):
        print(index)
        print(df[df.index == index]['title'].values[0])
        return df[df.index == index]['title'].values[0]

    def clean(title):
        return title.lower().strip().translate(str.maketrans('', '', string.punctuation))

    def get_index_from_title(title):
        cleaned_title = clean(title)
        matching_row = df[df['title'].apply(clean) == cleaned_title]
    
        if not matching_row.empty:
            return matching_row['index'].values[0].item()
        
    try:
        movie_index = get_index_from_title(title)
        similar_movies = sim_total[str(movie_index)]

        # return the similar movies
        recommendations = map(get_title_from_index, (similar_movies[:number_of_movies]))
        return recommendations
    
    # error handling
    except Exception as e:
        print(e)
        pass

    return recommendations

# debugging
# movie_list = recommend_movie('Tron', 7)
# print(movie_list)

#create_matrix()