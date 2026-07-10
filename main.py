import discord
from discord.ext import commands
import os
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home():
    return "Bot aktif!"
def run_web():
    app.run(host='0.0.0.0', port=8080)
Thread(target=run_web, daemon=True).start()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot aktif: {bot.user}")

bot.run(os.environ['DISCORD_TOKEN'])
