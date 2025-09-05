# Jordi Mursalim 2025
# Recommend a movie based on a given movie
# Data Wrangling based on TMDB Movie Dataset Analysis by Yinghao Zhang
# Text count vectorizer cosine similarity matrix based on Movie Recommendation by Mrinank Bhowmick

import numpy as np
import pandas as pd
import dotenv
import os
import csv
from sklearn.feature_extraction import text
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import LogisticRegression
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import string
import json
import random
import sys

#nltk.download('stopwords')
#nltk.download('punkt_tab')
#nltk.download('punkt')

stop_words = set(stopwords.words('english'))

file_sim_matrix = 'sim_matrix.csv'
file_sim_matrix_json = 'sim_matrix.json'
file_dataset = 'movie_db.csv'
file_ground_truth = 'train_db.json'

# This code has 2 uses:
# The first is to create a simularity matrix and save the top recommendations to json
#   *when the function is called
#
# The second is a function to recommend a movie based on that matrix
#   *when the function is called

# CREATING SIMULARITY MATRIX

def create_matrix():

# open the movie database csv file
    try:
        df = pd.read_csv(file_dataset)
        print('importing dataset')
    except Exception as e:
        print(e)
        sys.exit()

# columns = ['index', 'movie_id', 'title', 'genres', 'overview', 'keywords', 'runtime', 'origin_country', 'popularity',
#           'vote_count', 'vote_average', 'production_companies', 'release_date', 'budget', 'cast', 'director']

# lists of the features
    #feature_list = ['keywords', 'cast', 'genres', 'director', 'production_companies', 'origin_country', 'overview', 'num', 'time']
    text_features = ['keywords', 'cast', 'genres', 'director', 'production_companies', 'origin_country', 'overview'] # words
    num_features = ['release_date', 'vote_average', 'popularity', 'movie_id'] # numbers

# preprocessing to remove unused columns
    try:
        print('preprocessing dataframe')
        df.drop_duplicates(inplace=True)
        drop_columns = ['budget', 'runtime', 'vote_count']
        df.drop(drop_columns, axis=1, inplace=True)

# preprocessing to remove empty values
        for feature in text_features + num_features:
            df[feature] = df[feature].fillna("")
    except Exception as e:
        print(e)
        sys.exit()

# the ground truth data is formatted using the movie ids from TMDB, not the movie indexes from the data set I collected
# this function changes the movie id to the movie index in the dataset
    def get_index_from_id(movie_id):
        match = df[df.movie_id == movie_id]
        return match['index'].values[0] if not match.empty else None
    
    # import the ground truth for the logistic regression
    try:
        with open(file_ground_truth, 'r') as f:
            print('loading ground truth')
            id_ground_truth = json.load(f)
    except Exception as e:
        print(e)
        sys.exit()

    # process the json data of the ground truth from movie id to movie index
    print('converting ground truth formatting (movie_id to index)')
    converted_ground_truth = {}
    for key, movie_list in id_ground_truth.items():
        idx = get_index_from_id(int(key))
        if idx is None:
            continue
        sim_indices = [get_index_from_id(int(mid)) for mid in movie_list]
        sim_indices = [i for i in sim_indices if i is not None]
        if sim_indices:
            converted_ground_truth[idx] = sim_indices
    ground_truth = converted_ground_truth
        
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

# for text based data
# this segment of code gets the count vectors of the words used through the data set, then makes a cosine similarity

# creates matrices for each feature
    print('creating text cosine similarity matrices')
    s_keywords = cosine_similarity(CountVectorizer().fit_transform(df['keywords']))
    s_cast = cosine_similarity(CountVectorizer().fit_transform(df['cast']))
    s_genres = cosine_similarity(CountVectorizer().fit_transform(df['genres']))
    s_director = cosine_similarity(CountVectorizer().fit_transform(df['director']))
    s_production_companies = cosine_similarity(CountVectorizer().fit_transform(df['production_companies']))
    s_origin_country = cosine_similarity(CountVectorizer().fit_transform(df['origin_country']))
    s_overview = cosine_similarity(CountVectorizer().fit_transform(df['overview'].map(remove_stop_words)))

# for numerical data
# this segment of code normalizes numerical data then weighs their averages, then gets another cosine similarity
# popularity will use both a log transform and a min-max scaling
# the vote_average and release_date features will only be min-max scaled,
# release_date will also be treated as a seperate similarity, as I want to tune the weighting of the 3 similarities (text, numerical, release date)

    print('processing numerical data')
# creating scaler object
    scaler = MinMaxScaler()

# creating popularity column log scaled
    df['popularity_log'] = np.log(df['popularity'] + 1)

# scaling both popularity and vote_average with min-max
    for column in ['popularity_log', 'vote_average']:
        df[f'{column}_scaled'] = scaler.fit_transform(df[[column]])

    num_features = df[['popularity_log_scaled', 'vote_average_scaled']].values

    print('creating numerical cosine similarity matrix')
    s_num = cosine_similarity(num_features)

# new column for the release year
    df['release_year'] = pd.to_datetime(df['release_date'], errors='coerce').dt.year

# time based similarity formula that punishes if the film was made a long time from the target movie
    years = df['release_year'].values
    alpha = 0.05

# compute absolute differences across all pairs
    year_diff_matrix = np.abs(years[:, np.newaxis] - years[np.newaxis, :])

# apply exponential decay
    print('creating time similarity matrix')
    s_time = np.exp(-alpha * year_diff_matrix)

# clean each of the similarity matrices
    print('cleaning matrices')
    s_keywords = np.nan_to_num(s_keywords, nan=0.0)
    s_cast = np.nan_to_num(s_cast, nan=0.0)
    s_genres = np.nan_to_num(s_genres, nan=0.0)
    s_director = np.nan_to_num(s_director, nan=0.0)
    s_production_companies = np.nan_to_num(s_production_companies, nan=0.0)
    s_origin_country = np.nan_to_num(s_origin_country, nan=0.0)
    s_overview = np.nan_to_num(s_overview, nan=0.0)
    s_num = np.nan_to_num(s_num, nan=0.0)
    s_time = np.nan_to_num(s_time, nan=0.0)

# create training pairs for ML
    pairs = []
    labels = []

# takes the recommended training data as positives, where positives are 1
    print('creating training data')
    for movie, positives in ground_truth.items():
        positives = list(set(positives) & set(df['index']))

        for p in positives:
            pairs.append((movie, p))
            labels.append(1)

# generates negatives randomly from the rest of the movie pool where negatives are 0
        negatives = list(set(df['index']) - set(positives) - {movie})
        sampled_negs = random.sample(negatives, min(len(positives), len(negatives)))
        for n in sampled_negs:
            pairs.append((movie, n))
            labels.append(0)


    X = []
    for movie1, movie2 in pairs:
        features = [
            s_keywords[movie1, movie2],
            s_cast[movie1, movie2],
            s_genres[movie1, movie2],
            s_director[movie1, movie2],
            s_production_companies[movie1, movie2],
            s_origin_country[movie1, movie2],
            s_overview[movie1, movie2],
            s_num[movie1, movie2],
            s_time[movie1, movie2],
        ]
        X.append(features)
    
# plots the positive and negatives (labels) against the similarity pairs
    print('creating logistic regression')
    X = np.array(X)
    y = np.array(labels)

    model = LogisticRegression()
    model.fit(X, y)

# takes the coefficients of the logistic regression model as the weights of each of the matrices
    weights = model.coef_[0]
    print("learned weights are:", weights)

# assigns the learned weights
    w_keywords = weights[0]
    w_cast = weights[1]
    w_genres = weights[2]
    w_director = weights[3]
    w_production_companies = weights[4]
    w_origin_country = weights[5]
    w_overview = weights[6]
    w_num = weights[7]
    w_time = weights[8]

# total simularity matrix of all the features
    sim_matrix_total = ( w_keywords * s_keywords + w_cast * s_cast + w_genres * s_genres + w_director * s_director + w_production_companies * s_production_companies + w_origin_country * s_origin_country + w_overview * s_overview + w_num * s_num + w_time * s_time)

# since the dataset will be large, we are turning it into a json with the first 20 most similar movies saved.
    print('sorting similar movies')
    sorted_sim_matrix = {}
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

    try:
        with open(file_sim_matrix_json, mode='w', encoding='utf-8') as file_out:
            print('exporting similar movies')
            json.dump(sorted_sim_matrix, file_out)
    except Exception as e:
        print(f'error occured: {e}')

    print('process complete')



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