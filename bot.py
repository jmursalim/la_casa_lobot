# Jordi Mursalim 2025
# Commands for the discord bot
# imports the webscraping function for letterboxd movies

import discord
from discord.ext import commands
from discord import app_commands
import random
import scraper
from recommend import recommend_movie
from collections import deque
from dotenv import load_dotenv
import yt_dlp
import os
import asyncio

# bot token is stored in a .env file
load_dotenv()
token = os.getenv('TOKEN')

character_limit = 2000

SONG_QUEUES = {}

async def search_ytdlp_async(query, ydl_opts):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: _extract(query, ydl_opts))

def _extract(query, ydl_opts):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(query, download=False)

# setting up bot command details
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

# start-up message for the bot
    async def on_ready(self):
        await self.tree.sync()
        print('Logged on as {0}!'.format(self.user))

bot = MyClient()

@bot.tree.command(name="skip", description="Skips the current playing song")
async def skip(interaction: discord.Interaction):
    if interaction.guild.voice_client and (interaction.guild.voice_client.is_playing() or interaction.guild.voice_client.is_paused()):
        interaction.guild.voice_client.stop()
        await interaction.response.send_message("Skipped the current song.")
    else:
        await interaction.response.send_message("Not playing anything to skip.")


@bot.tree.command(name="pause", description="Pause the currently playing song.")
async def pause(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client

    # Check if the bot is in a voice channel
    if voice_client is None:
        return await interaction.response.send_message("I'm not in a voice channel.")

    # Check if something is actually playing
    if not voice_client.is_playing():
        return await interaction.response.send_message("Nothing is currently playing.")
    
    # Pause the track
    voice_client.pause()
    await interaction.response.send_message("Playback paused!")


@bot.tree.command(name="resume", description="Resume the currently paused song.")
async def resume(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client

    # Check if the bot is in a voice channel
    if voice_client is None:
        return await interaction.response.send_message("I'm not in a voice channel.")

    # Check if it's actually paused
    if not voice_client.is_paused():
        return await interaction.response.send_message("I’m not paused right now.")
    
    # Resume playback
    voice_client.resume()
    await interaction.response.send_message("Playback resumed!")


@bot.tree.command(name="stop", description="Stop playback and clear the queue.")
async def stop(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client

    # Check if the bot is in a voice channel
    if not voice_client or not voice_client.is_connected():
        return await interaction.response.send_message("I'm not connected to any voice channel.")

    # Clear the guild's queue
    guild_id_str = str(interaction.guild_id)
    if guild_id_str in SONG_QUEUES:
        SONG_QUEUES[guild_id_str].clear()

    # If something is playing or paused, stop it
    if voice_client.is_playing() or voice_client.is_paused():
        voice_client.stop()

    # (Optional) Disconnect from the channel
    await voice_client.disconnect()

    await interaction.response.send_message("Stopped playback and disconnected!")


@bot.tree.command(name="play", description="Play a song or add it to the queue.")
@app_commands.describe(song_query="Search query")
async def play(interaction: discord.Interaction, song_query: str):
    await interaction.response.defer()

    voice_channel = interaction.user.voice.channel

    if voice_channel is None:
        await interaction.followup.send("You must be in a voice channel.")
        return

    voice_client = interaction.guild.voice_client

    if voice_client is None:
        voice_client = await voice_channel.connect()
    elif voice_channel != voice_client.channel:
        await voice_client.move_to(voice_channel)

    ydl_options = {
        "playlist-items": "1",
        "format": "bestaudio[abr<=96]/bestaudio",
        "noplaylist": True,
        "youtube_include_dash_manifest": False,
        "youtube_include_hls_manifest": False,
    }

    query = "ytsearch1: " + song_query
    results = await search_ytdlp_async(query, ydl_options)
    tracks = results.get("entries", [])

    if tracks is None:
        await interaction.followup.send("No results found.")
        return

    first_track = tracks[0]
    audio_url = first_track["url"]
    title = first_track.get("title", "Untitled")

    guild_id = str(interaction.guild_id)
    if SONG_QUEUES.get(guild_id) is None:
        SONG_QUEUES[guild_id] = deque()

    SONG_QUEUES[guild_id].append((audio_url, title))

    if voice_client.is_playing() or voice_client.is_paused():
        await interaction.followup.send(f"Added to queue: **{title}**")
    else:
        await interaction.followup.send(f"Now playing: **{title}**")
        await play_next_song(voice_client, guild_id, interaction.channel)


async def play_next_song(voice_client, guild_id, channel):
    if SONG_QUEUES[guild_id]:
        audio_url, title = SONG_QUEUES[guild_id].popleft()

        ffmpeg_options = {
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            "options": "-vn -c:a libopus -b:a 96k",
            # Remove executable if FFmpeg is in PATH
        }

        source = discord.FFmpegOpusAudio(audio_url, **ffmpeg_options, executable="bin\\ffmpeg\\ffmpeg.exe")

        def after_play(error):
            if error:
                print(f"Error playing {title}: {error}")
            asyncio.run_coroutine_threadsafe(play_next_song(voice_client, guild_id, channel), bot.loop)

        voice_client.play(source, after=after_play)
        asyncio.create_task(channel.send(f"Now playing: **{title}**"))
    else:
        await voice_client.disconnect()
        SONG_QUEUES[guild_id] = deque()

# hello command
@bot.tree.command()
async def hello(interaction: discord.Interaction):
    await interaction.send('Hello world!')

@bot.tree.command()
async def command_list(interaction):
    message = '$watchlist *letterboxd_username*: prints the watchlist of a letterboxd user\n' \
              '$watchlist_pool *letterboxd_username_1* *letterboxd_username_2* *...*: prints the combined watchlists of multiple users\n' \
              '$random_watchlist *letterboxd_username*: prints a random movie from a letterboxd user\'s watchlist\n' \
              '$random_watchlist_pool *letterboxd_username_1* *letterboxd_username_2* *...*: prints a random movie from the combined watchlists of multiple users\n' \
              '$recommend *movie_title*, *number_of_recommendations*: prints a list of similar movies\n' \
              '$coinflip: flips a coin\n'
    
    await interaction.send(message)


# sends a letterboxd watchlist
# parameters: letterboxd username
# use: $watchlist username
@bot.tree.command(name='watchlist', description='Print the watchlist of a letterboxd user')
@app_commands.describe(username="Letterboxd username")
async def watchlist(interaction: discord.Interaction, username : str):
    """
    $watchlist *letterboxd_username*: prints the watchlist of a letterboxd user
    """
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
        await interaction.send(f'Error: retrieving watchlist')

    # iterates the list so the discord message doesnt exceed the character limit
    total_watchlist = str(total_watchlist)
    if len(total_watchlist) > character_limit:
        await interaction.send(f'the user {username}\'s watchlist is')
        for character in range(0, len(total_watchlist), character_limit):
            if character > len(total_watchlist):
                await interaction.send(total_watchlist[character:len(total_watchlist)])
            else:
                await interaction.send(total_watchlist[character:character+character_limit])

    # send the message if the message is under the character limit
    else:
        await interaction.send(f'The user {username}\'s watchlist is \n{total_watchlist}')

# gives a random movie from a letterboxd watchlist
# parameters: letterboxd username
# use: $random_watchlist username
@bot.tree.command(name='random_watchlist', description='Print a random movie from the watchlist of a letterboxd user')
@app_commands.describe(username="Letterboxd username")
async def random_watchlist(interaction: discord.Interaction, username : str):
    """
    $random_watchlist *letterboxd_username*: prints a random movie from a letterboxd user's watchlist
    """
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
        await interaction.send(f'Error: retrieving watchlist')
    # choose a random movie from the list
    movie = random.choice(total_watchlist)

    # send message with the movie
    await interaction.send(f'Random movie from {username}\'s watchlist is \n{movie}')

# gives a random movie from the watchlist of multiple users
# parameters: multiple letterboxd usernames
# use: $random_watchlist_pool user1 user2 user3 ...
@bot.tree.command(name='random_watchlist_pool', description='Print a random movie from a pool of watchlists')
@app_commands.describe(username_pool="Letterboxd usernames seperated by spaces")
async def random_watchlist_pool(interaction: discord.Interaction, username_pool: str):
    """
    $random_watchlist_pool *letterboxd_username_1* *letterboxd_username_2* *...*: prints a random movie from the combined watchlists of multiple users
    """
    try:
        #initialize variables
        total_watchlist = []
        
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
                # print(total_watchlist)

        # choose a random movie
        movie = random.choice(list(set(total_watchlist)))

        # send movie as a message
        await interaction.send(f'Random movie from {username_pool} watchlist is \n{movie}')

    except ValueError:
        await interaction.send('Error: invalid inputs')

# send the combined watchlist of multiple users
# parameters: multiple letterboxd usernames
# use: $watchlist_pool user1 user2 user3 ...
@bot.tree.command(name='watchlist_pool', description='Print the watchlists from a pool of users')
async def watchlist_pool(interaction: discord.Interaction):
    """
    $watchlist_pool *letterboxd_username_1* *letterboxd_username_2* *...*: prints the combined watchlists of multiple users
    """
    try:
        # initialize variables
        total_watchlist = []
        username_pool = str(interaction.message.content).replace('$watchlist_pool ', '').split()
        
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
                # print(total_watchlist)

        # change total watchlist from list to string
        total_watchlist = str(total_watchlist)

        # iterates the list so the discord message doesnt exceed the character limit
        if len(total_watchlist) > character_limit:
            await interaction.send(f'the user {username_pool}\'s watchlist is')
            for character in range(0, len(total_watchlist), character_limit):
                if character > len(total_watchlist):
                    await interaction.send(total_watchlist[character:len(total_watchlist)])
                else:
                    await interaction.send(total_watchlist[character:character+character_limit])

        else:
            # send movie as a message
            await interaction.send(f'The user {username_pool}\'s watchlist is \n{total_watchlist}')

    except ValueError:
        await interaction.send('Invalid inputs')

# coinflip command outputs heads or tails
@bot.tree.command(name='coinflip', description='flip a coin')
async def coinflip(interaction: discord.Interaction):
    """
    $coinflip: flips a coin
    """
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

    await interaction.send('Flipping coin:')
    message = await interaction.send('-')
    print('-')

    #coin flip animation
    for i in range(1,10):
        frame = i % 4
        await asyncio.sleep(0.2)
        await message.edit(content=coin_animation[frame])
        print(coin_animation[frame])

    #send result of flip
    await interaction.send(coin_results[result])

# recommend a movie
# parameters: movie they want similar movies to, number of recommendations
# use: $recommend movie_title,number_of_recommendations
@bot.tree.command(name="recommend", description="Recommend a movie")
async def recommend(interaction: discord.Interaction):
    """
    $recommend *movie_title*, *number_of_recommendations*: prints a list of similar movies
    """
    try:
        # handling the input message
        message_list = str(interaction.message.content).replace('$recommend ', '').split(', ')
        print(message_list)
        movie_title = message_list[0]
        number_of_recommendations = int(message_list[1])
    
        # get movie recommendations
        recommendation_list = recommend_movie(movie_title, number_of_recommendations)

        # send message to chat
        await interaction.send(f'Movie recommendations for {movie_title}:')
        message = ''
        for movie in recommendation_list:
            message = message + movie + '\n'
        print(message)
        await interaction.send(message)

    except Exception as e:
        await interaction.send(f'Error occured: {e}')

bot.run(str(token))