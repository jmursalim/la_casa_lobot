import requests
import json
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os

load_dotenv()

user_agent = os.getenv('USER_AGENT')
accept_language = os.getenv('ACCEPT_LANGUAGE')

def get_movie_details(username: str, page_number) -> dict:
    
    headers = {
        'User-Agent': user_agent,
        'Accept-Language': accept_language
    }
    watchlist_url = f'https://letterboxd.com/{username}/watchlist/page/{page_number}/'

    movie_details = []

    page = requests.get(watchlist_url, headers=headers)
    soup = BeautifulSoup(page.content, features='lxml')

    try:
        posters = soup.find_all(
            "li", class_="poster-container"
        )

        for poster in posters:
            div = poster.find('div', class_='film-poster')
            if div and div.find('img'):
                title = div.find('img')['alt']
                movie_details.append(title)

    except Exception as e:
        print('Could not fetch watchlist details')
        print(f'Failed with exception: {e}')

    return movie_details