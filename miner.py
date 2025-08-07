# Jordi Mursalim 2025
# Dataminer for the TMDB api

from dotenv import load_dotenv
import os
import pandas as pd
import numpy as np
import tmdbsimple as tmdb
import requests
import csv

# load api token
load_dotenv()
tmdb.API_KEY = os.getenv('TMDB_API_KEY')
tmdb.REQUESTS_TIMEOUT = 5
tmdb.REQUESTS_SESSION = requests.Session()

# constants
columns = ['index', 'movie_id', 'title', 'genres', 'overview', 'keywords', 'runtime', 'origin_country', 'popularity', 'vote_count', 'vote_average', 'production_companies', 'release_date', 'budget', 'cast', 'director']
main_cast = 4
file = 'movie_db.csv'
config_file = 'miner_config.txt'

# get the directory of the miner
miner_dir = os.path.dirname(__file__)
config_path = os.path.join(miner_dir, config_file)

# get variables from config file
config_vars = {}
try:
    with open(config_path, 'r') as f:
        for line in f:
            line = line.strip()  # Remove leading/trailing whitespace and newlines
            if line and '=' in line:
                key, value = line.split('=', 1)
                config_vars[key.strip()] = value.strip()
except FileNotFoundError:
    print(f"Error: The file '{config_file}' was not found at '{config_path}'")
except Exception as e:
    print(f"An error occurred while reading the file: {e}")

# update miner settings through the config
start_id = int(config_vars.get('START_ID'))
end_id = int(config_vars.get('END_ID'))
init_file = int(config_vars.get('INIT_FILE'))
index = int(config_vars.get('INDEX'))

# initialize the csv file with the headers
if init_file == 1:
    with open(file, 'w', newline='') as f:
        csv_writer = csv.writer(f)
        csv_writer.writerow(columns)
        print('initializing csv file')

# function to get the genres as a list
def get_genres(genres_dict):
    genres = []
    for item in genres_dict:
        genres.append(item.get('name'))
    return genres

# function to get the keywords as a list
def get_keywords(keywords_dict):
    keywords = []
    for item in keywords_dict.get('keywords'):
        keywords.append(item.get('name'))
    return keywords

# function to get the production companies as a list
def get_production_companies(production_companies_dict):
    production_companies = []
    for item in production_companies_dict:
        production_companies.append(item.get('name'))
    return production_companies

# function to get the director
def get_director(credits):
    director_name = None
    for member in credits.get("crew", []):
        if member.get("job").lower() == "director":
            director_name = member.get("name")
            return director_name
            break

# function to get the main cast
def get_cast(credits, actors):
    cast = []
    for member in credits.get("cast", []):
        if member.get("order") < actors:
            cast.append(member.get("name"))
    return cast

# iterate through each movie id available on tmdb
for movie_id in range(start_id, end_id):
    movie = tmdb.Movies(movie_id)
    # print(f'movie id is {movie_id}')

    try:
        response = movie.info()
        credits = movie.credits()
        
        # Check if the movie has more than 300 votes, to ensure the dataset isn't too bloated
        if movie.vote_count < 300 :
            # print('movie has less than 300 votes')
            pass
        else :
            df = pd.DataFrame(
                {
                    'index' : index,
                    'movie_id' : movie_id,
                    'title' : movie.title,
                    'genres' : [get_genres(movie.genres)],
                    'overview' : movie.overview,
                    'keywords' : [get_keywords(movie.keywords())],
                    'runtime' : movie.runtime,
                    'origin_country' : [movie.origin_country],
                    'popularity' : movie.popularity,
                    'vote_count' : movie.vote_count,
                    'vote_average' : movie.vote_average,
                    'production_companies' : [get_production_companies(movie.production_companies)],
                    'release_date' : pd.Timestamp(movie.release_date),
                    'budget' : movie.budget,
                    'cast' : [get_cast(credits, main_cast)],
                    'director' : get_director(credits)
                }
            )
            # print(f'getting dataframe for {response.get('title')}')

            # add data to csv file
            df.to_csv(file, mode='a', header=False, index=False)
            index += 1
        
    except Exception as e:
        #print(f'exception occured : {e}')
        pass

print('task finished')