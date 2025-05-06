import discord
import asyncio
import yt_dlp
import datetime
from discord import FFmpegPCMAudio
from discord.ext import commands, tasks

# GuildID and Bot Token

guild_id = ""
token = ""

# yt-dlp Settings

ydl_opts = {
    "quiet": True,
    "noplaylist": True,
    "format": "bestaudio[ext=m4a]/bestaudio/best",
}


# yt-dlp Functions

# Gets Info From Video URL


def get_info(url: str):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
    return info


# Gets Source From Video Stream URL

def get_source(url: str):
    source = FFmpegPCMAudio(url)
    return source


# Global Variables

music_queue = asyncio.Queue()
current_channel = None
current_client = None
inactive = 0
paused = False

# Initialize Bot

command_prefix = "/"

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

guild = discord.Object(guild_id)

client = commands.Bot(command_prefix=command_prefix, intents=intents)


# Bot Initialization

@client.event
async def on_ready():
    # Sync Slash Commands

    try:
        synced = await client.tree.sync(guild=guild)
        print(f"Synced {len(synced)} commands to {guild.id}")
    except Exception as e:
        print(f"Error syncing commands: {e}")

    # Start Background Task Loops
    playNext.start()
    inactivity.start()


# Main Function

# Queueing Music

@client.tree.command(name="play", description="Plays track from Youtube url", guild=guild)
async def play(interaction, url: str):
    global paused

    await interaction.response.defer()

    # If user is in voice, check the channel is valid
    if interaction.user.voice:

        global current_channel
        global current_client

        current_channel = interaction.channel
        user_channel = interaction.user.voice.channel
        voice_client = interaction.guild.voice_client
        current_client = voice_client

        video_info = get_info(url)
        video_source = get_source(video_info["url"])

        paused = False

        # If not in a voice channel, connect to user's channel and update voice_client
        if voice_client is None:
            voice_client = await user_channel.connect()
            current_client = voice_client

        # If in a different voice channel, disconnect from that first then connect to user's channel
        elif user_channel != voice_client.channel:
            await voice_client.disconnect()
            await user_channel.connect()

        # Since it is now in the user's voice channel, if queue is emtpy, play music, otherwise queue it

        if not voice_client.is_playing():
            voice_client.play(video_source)
            await interaction.followup.send(f"Now playing: {video_info['title']} | "
                                            f"Duration: {datetime.timedelta(seconds=video_info['duration'])}.")
        else:
            await music_queue.put(video_info)
            await interaction.followup.send(f"Queued: {video_info['title']} | "
                                            f"Duration: {datetime.timedelta(seconds=video_info['duration'])}")

    else:
        await interaction.followup.send("User is not connected to any voice channels.")


# Skipping Music

@client.tree.command(name="skip", description="Skips to next track in queue", guild=guild)
async def skip(interaction):
    global paused

    # If the queue is not empty, stop the bot and

    if current_client is not None and current_channel is not None:
        if not music_queue.empty():
            paused = False
            current_client.stop()
            await interaction.response.send_message(f"Skipping to next track.")
        else:
            if current_client.is_playing() or paused:
                paused = False
                current_client.stop()
            await interaction.response.send_message("Queue is empty.")
    else:
        await interaction.response.send_message("I'm not currently playing music.")


# Pauses Bot
@client.tree.command(name="pause", description="Pauses current track", guild=guild)
async def pause(interaction):
    global paused

    if current_client is not None and current_channel is not None:
        if current_client.is_playing() and not paused:
            paused = True
            current_client.pause()
            await interaction.response.send_message("Paused current track.")
        else:
            await interaction.response.send_message("I'm not currently playing music.")
    else:
        await interaction.response.send_message("I'm not currently playing music.")


# Resumes Bot
@client.tree.command(name="resume", description="Resumes current track", guild=guild)
async def resume(interaction):
    global paused

    if current_client is not None and current_channel is not None:
        if not current_client.is_playing() and paused:
            paused = False
            current_client.resume()
            await interaction.response.send_message("Resumed current track.")
        else:
            await interaction.response.send_message("I'm not currently playing music.")
    else:
        await interaction.response.send_message("I'm not currently playing music.")


# Background Tasks

# Checks to play next music in queue
@tasks.loop(seconds=1)
async def playNext():
    # If queue is empty, or it's not in a voice channel, do nothing

    if music_queue.empty() or current_client is None or not current_client.is_connected():
        return

    # Since queue is not empty and the bot is in a voice channel,
    # check if current channel and current client is not None

    if current_channel is not None and current_client is not None:

        # Since current channel and current client exists, play the next song in queue if it isn't already playing

        if not current_client.is_playing() and not paused:
            video_info = await music_queue.get()
            video_source = get_source(video_info["url"])

            current_client.play(video_source)
            await current_channel.send(f"Now playing: {video_info['title']} | "
                                       f"Duration: {datetime.timedelta(seconds=video_info['duration'])}.")


# Checks for Inactivity

@tasks.loop(seconds=1)
async def inactivity():
    global inactive
    global current_client
    global current_channel

    if current_client is not None:
        # If Bot is playing, set inactive timer to 0, otherwise, add 1 to it

        if current_client.is_playing():
            inactive = 0
        else:
            inactive += 1

        # If inactive timer reaches 10 minutes, disconnect the bot

        if inactive >= 600:
            await current_client.disconnect()
            current_client = None
            await current_channel.send("Disconnected due to inactivity.")
            current_channel = None


# Run Bot

client.run(token)
