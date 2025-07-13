import requests
import json
from bs4 import BeautifulSoup



def get_movie_details(username: str, page_number) -> dict:
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8'
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

watchlist = get_movie_details('declammm', 3)
print(watchlist)