# Jordi Mursalim 2025
# Webscraper takes data from letterboxd
# This is currently used to get the list of movies on a user's watchlist, the data scraping can be changed to include other details of a movie

import requests
import json
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os

# load the .env file that holds the webscraping permissions
load_dotenv()
user_agent = os.getenv('USER_AGENT')
accept_language = os.getenv('ACCEPT_LANGUAGE')

# function to get the movie data from a letterboxd watchlist with the parameters of the username and watchlist page
def get_movie_details(username: str, page_number) -> dict:
    
    # credentials for beautiful soup to send requests to letterboxd
    headers = {
        'User-Agent': user_agent,
        'Accept-Language': accept_language
    }

    # url of letterboxd watchlists
    watchlist_url = f'https://letterboxd.com/{username}/watchlist/page/{page_number}/'

    # initialize empty watchlist
    movie_details = []

    # initialize beautiful soup of letterboxd watchlist
    page = requests.get(watchlist_url, headers=headers)
    soup = BeautifulSoup(page.content, features='lxml')

    try:
        # find poster-container class in html
        posters = soup.find("ul", {"class": "grid -p125 -scaled128"})

        # iterate through each poster
        for item in posters.find_all("li", {"class": "griditem"}):
            
            # this div has the movie details
            comp = item.find("div", {"class": "react-component"})

            # get the movie title from the alt text of the image
            if comp:
                title = comp.get("data-item-full-display-name")
                movie_details.append(title)
                
        return movie_details

    except Exception as e:
        print('Could not fetch watchlist details')
        print(f'Failed with exception: {e}')

        return ValueError