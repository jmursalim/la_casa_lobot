# Jordi Mursalim 2025
# Gets the dataset to train the machine learning of the weightings

from dotenv import load_dotenv
import os
import tmdbsimple as tmdb
import requests
import json

# load api token
load_dotenv()
tmdb.API_KEY = os.getenv('TMDB_API_KEY')
tmdb.REQUESTS_TIMEOUT = 5
tmdb.REQUESTS_SESSION = requests.Session()

data_dir = "data"
file = 'train_db.json'
config_file = 'train_config.txt'

# get the directory of the output file
train_dir = os.path.dirname(os.path.abspath(__file__))
grandparent_dir = os.path.abspath(os.path.join(train_dir, os.pardir, os.pardir))
db_path = os.path.join(grandparent_dir, data_dir, file)

# get the directory of the config
config_path = os.path.join(grandparent_dir, config_file)

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
interval = int(config_vars.get('INTERVAL'))

# load the json object
if init_file == 0 and os.path.exists(file):
    with open(file, 'r') as f:
        data = json.load(f)
else:
    data = {}

for movie_id in range(start_id, end_id, interval):
    try:
        movie = tmdb.Movies(movie_id)
        recs = movie.recommendations()
        similar_movies = [rec["id"] for rec in recs.get("results", [])]
        data[movie_id] = similar_movies
    except Exception as e:
        print(f"Error with movie {movie_id}: {e}")
        pass

with open(db_path, 'w') as f:
    json.dump(data, f, indent=2)