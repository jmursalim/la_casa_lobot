# Jordi Mursalim 2025
# Commands for the discord bot
# imports the webscraping function for letterboxd movies

import discord
from discord.ext import commands
import random
import scraper
from dotenv import load_dotenv
import os
import asyncio

# bot token is stored in a .env file
load_dotenv()
token = os.getenv('TOKEN')

character_limit = 2000

# setting up bot command details
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='$', intents=intents)

# start-up message for the bot
@bot.event
async def on_ready():
    print('Logged on as {0}!'.format(bot.user))

# hello command
@bot.command()
async def hello(ctx):
    await ctx.send('Hello world!')

# sends a letterboxd watchlist
# parameters: letterboxd username
# use: $watchlist username
@bot.command()
async def watchlist(ctx, username : str):
    # initialize variables
    page_number = 1
    total_watchlist = []

    # iterate through each page of the letterboxd watchlist with the webscraper
    try:
        while scraper.get_movie_details(username, page_number) != []:
            print(f'Requesting page {page_number} of watchlist')
            page_content = scraper.get_movie_details(username, page_number)
            total_watchlist += page_content
            page_number += 1
    except ValueError:
        await ctx.send(f'Error: retrieving watchlist')

    # iterates the list so the discord message doesnt exceed the character limit
    total_watchlist = str(total_watchlist)
    if len(total_watchlist) > character_limit:
        await ctx.send(f'the user {username}\'s watchlist is')
        for character in range(0, len(total_watchlist), character_limit):
            if character > len(total_watchlist):
                await ctx.send(total_watchlist[character:len(total_watchlist)])
            else:
                await ctx.send(total_watchlist[character:character+character_limit])

    # send the message if the message is under the character limit
    else:
        await ctx.send(f'The user {username}\'s watchlist is \n{total_watchlist}')

# gives a random movie from a letterboxd watchlist
# parameters: letterboxd username
# use: $random_watchlist username
@bot.command()
async def random_watchlist(ctx, username : str):
    # initialize variables
    page_number = 1
    total_watchlist = []

    # iterate through each page of the letterboxd watchlist with the webscraper
    try:
        while scraper.get_movie_details(username, page_number) != []:
            print(f'Requesting page {page_number} of watchlist')
            page_content = scraper.get_movie_details(username, page_number)
            total_watchlist += page_content
            page_number += 1
    except ValueError:
        await ctx.send(f'Error: retrieving watchlist')
    # choose a random movie from the list
    movie = random.choice(total_watchlist)

    # send message with the movie
    await ctx.send(f'Random movie from {username}\'s watchlist is \n{movie}')

# gives a random movie from the watchlist of multiple users
# parameters: multiple letterboxd usernames
# use: $random_watchlist_pool user1,user2,user3,...
@bot.command()
async def random_watchlist_pool(ctx, username_pool_spaced : str):
    try:
        #initialize variables
        total_watchlist = []
        username_pool = username_pool_spaced.split(',')
        
        # debugging
        # print(username_pool_spaced)
        # print(username_pool)

        # iterate through the watchlist pages of each user
        for username in username_pool:
            page_number = 1

            while scraper.get_movie_details(username, page_number) != []:
                print(f'Requesting page {page_number} of watchlist')
                page_content = scraper.get_movie_details(username, page_number)
                total_watchlist += page_content
                page_number += 1
                print(total_watchlist)

        # choose a random movie
        movie = random.choice(list(set(total_watchlist)))

        # send movie as a message
        await ctx.send(f'Random movie from {username_pool} watchlist is \n{movie}')

    except ValueError:
        await ctx.send('Error: invalid inputs')

# send the combined watchlist of multiple users
# parameters: multiple letterboxd usernames
# use: $watchlist_pool user1,user2,user3,...
@bot.command()
async def watchlist_pool(ctx, username_pool_spaced : str):
    try:
        # initialize variables
        total_watchlist = []
        username_pool = username_pool_spaced.split(',')
        
        # debugging
        # print(username_pool)
        # print(username_pool_spaced)

        # iterate through the watchlist pages of each user
        for username in username_pool:
            page_number = 1

            while scraper.get_movie_details(username, page_number) != []:
                print(f'Requesting page {page_number} of watchlist')
                page_content = scraper.get_movie_details(username, page_number)
                total_watchlist += page_content
                page_number += 1
                print(total_watchlist)

        # change total watchlist from list to string
        total_watchlist = str(total_watchlist)

        # iterates the list so the discord message doesnt exceed the character limit
        if len(total_watchlist) > character_limit:
            await ctx.send(f'the user {username}\'s watchlist is')
            for character in range(0, len(total_watchlist), character_limit):
                if character > len(total_watchlist):
                    await ctx.send(total_watchlist[character:len(total_watchlist)])
                else:
                    await ctx.send(total_watchlist[character:character+character_limit])

        else:
            # send movie as a message
            await ctx.send(f'The user {username}\'s watchlist is \n{total_watchlist}')

    except ValueError:
        await ctx.send('Invalid inputs')

# coinflip command outputs heads or tails
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