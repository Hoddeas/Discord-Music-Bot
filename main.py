import discord
import asyncio
import yt_dlp
import datetime
from discord import FFmpegPCMAudio
from discord.ext import commands

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
    try:
        synced = await client.tree.sync(guild=guild)
        print(f"Synced {len(synced)} commands to {guild.id}")
    except Exception as e:
        print(f"Error syncing commands: {e}")


# Main Function

@client.tree.command(name="play", description="test", guild=guild)
async def play(interaction, url: str):
    await interaction.response.defer()

    # If user is in voice, check the channel is valid
    if interaction.user.voice:

        user_channel = interaction.user.voice.channel

        voice_client = interaction.guild.voice_client

        video_info = get_info(url)
        video_source = get_source(video_info["url"])

        # If not in a voice channel, connect to user's channel and update voice_client
        if voice_client is None:
            await user_channel.connect()
            voice_client = interaction.guild.voice_client
        # If in a different voice channel, disconnect from that first then connect to user's channel
        elif user_channel != voice_client.channel:
            await voice_client.disconnect()
            await user_channel.connect()

        # Since it is now in the user's voice channel, play audio
        await interaction.followup.send(f"Now playing: {video_info['title']} | "
                                                f"Duration: {datetime.timedelta(seconds=video_info['duration'])}.")

        voice_client.play(video_source)

    else:
        await interaction.response.send_message("User not connected to any voice channels.")


@client.tree.command(name="leave", description="test", guild=guild)
async def leave(interaction):
    voice_client = interaction.guild.voice_client
    if voice_client:
        await voice_client.disconnect()
        await interaction.response.send_message("left channel")
    else:
        await interaction.response.send_message("coundlt leave")


# Run Bot

client.run(token)
