import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import os


bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

@bot.event
async def post_to_channel(channel_id, cf, name):
  channel = bot.get_channel(channel_id)
  
  embed = discord.Embed(title=f"{name}",
  url=f"https://app.cftools.cloud/profile/{cf}",
  colour=0x595959)
  await channel.send(embed=embed)

@bot.event
async def on_ready():
  print("Bot is online and active.")


async def bot_start():
  await bot.start(os.environ['DISCORDTOKEN'])
  print("Bot is starting! Please wait...")


