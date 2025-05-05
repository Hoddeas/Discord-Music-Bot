import discord
from discord.ext import commands

# Initialize Bot

command_prefix = "/"

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

guild = discord.Object("ID")

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

@client.tree.command(name="play", description="Adds chosen music to queue", guild=guild)
async def play(interaction):
    if interaction.user.voice and interaction.user.voice.channel:
        channel = interaction.user.voice.channel
        await channel.connect()
        await interaction.response.send_message("Joined channel")
    else:
        await interaction.response.send_message("coundlt sjoin")

# Run Bot

client.run("ID")

