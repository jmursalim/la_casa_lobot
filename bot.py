import discord
from discord.ext import commands
import random
import scraper

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

bot.run('MTM5Mzc0NTI0NTI5MTgwNjc3MQ.Gxbs8A.Ky37_OeUx6zyrvt1W3SnHokBLNC12gK-ATIgDo')