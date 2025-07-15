import discord
from discord.ext import commands
import random
import scraper
from dotenv import load_dotenv
import os
import asyncio

load_dotenv()

token = os.getenv('TOKEN')

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='$', intents=intents)

@bot.event
async def on_ready():
    print('Logged on as {0}!'.format(bot.user))

@bot.command()
async def hello(ctx):
    await ctx.send('Hello world!')

@bot.command()
async def watchlist(ctx, username : str):
    page_number = 1
    total_watchlist = []

    while scraper.get_movie_details(username, page_number) != []:
        print(f'Requesting page {page_number} of watchlist')
        page_content = scraper.get_movie_details(username, page_number)
        total_watchlist += page_content
        page_number += 1

    await ctx.send(f'The user {username}\'s watchlist is \n{total_watchlist}')

@bot.command()
async def random_watchlist(ctx, username : str):
    page_number = 1
    total_watchlist = []

    while scraper.get_movie_details(username, page_number) != []:
        print(f'Requesting page {page_number} of watchlist')
        page_content = scraper.get_movie_details(username, page_number)
        total_watchlist += page_content
        page_number += 1

    movie = random.choice(total_watchlist)

    await ctx.send(f'Random movie from {username}\'s watchlist is \n{movie}')

@bot.command()
async def random_watchlist_pool(ctx, username_pool_spaced : str):
    try:
        total_watchlist = []
        print(username_pool_spaced)
        username_pool = username_pool_spaced.split(',')
        print(username_pool)

        for username in username_pool:
            page_number = 1

            while scraper.get_movie_details(username, page_number) != []:
                print(f'Requesting page {page_number} of watchlist')
                page_content = scraper.get_movie_details(username, page_number)
                total_watchlist += page_content
                page_number += 1
                print(total_watchlist)

        movie = random.choice(list(set(total_watchlist)))

        await ctx.send(f'Random movie from {username_pool} watchlist is \n{movie}')

    except ValueError:
        await ctx.send('Invalid inputs')

@bot.command()
async def watchlist_pool(ctx, username_pool_spaced : str):
    try:
        total_watchlist = []
        print(username_pool_spaced)
        username_pool = username_pool_spaced.split(',')
        print(username_pool)

        for username in username_pool:
            page_number = 1

            while scraper.get_movie_details(username, page_number) != []:
                print(f'Requesting page {page_number} of watchlist')
                page_content = scraper.get_movie_details(username, page_number)
                total_watchlist += page_content
                page_number += 1
                print(total_watchlist)

        await ctx.send(f'total watchlist from {username_pool}  is \n{list(set(total_watchlist))}')

    except ValueError:
        await ctx.send('Invalid inputs')

@bot.command()
async def coinflip(ctx):
    # - / | \
    coin_animation = {
        1 : '-',
        2 : '/',
        3 : '|',
        0 : '\\'
    }
    coin_results = {
        0:'Heads!',
        1:'Tails!'
    }

    result = random.randint(0,1)

    await ctx.send('Flipping coin:')
    message = await ctx.send('-')
    print('-')

    #coin flip animation
    for i in range(1,10):
        frame = i % 4
        await asyncio.sleep(0.2)
        await message.edit(content=coin_animation[frame])
        print(coin_animation[frame])

    #send result of flip
    await ctx.send(coin_results[result])


bot.run(str(token))