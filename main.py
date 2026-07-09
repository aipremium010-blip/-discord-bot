import discord
from discord.ext import commands
import os
from flask import Flask
from threading import Thread

# === WEB SERVER (Render'in botu aktif gormesi icin) ===
app = Flask('')

@app.route('/')
def home():
    return "Bot aktif! 🚀"

def run_web():
    app.run(host='0.0.0.0', port=8080)

Thread(target=run_web).start()

# === DISCORD BOT ===
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ {bot.user} aktif!")

@bot.command()
async def selam(ctx):
    await ctx.send(f"Selam {ctx.author.mention}! 👋")

@bot.command()
async def ping(ctx):
    await ctx.send(f"Pong! 🏓 Gecikme: {round(bot.latency * 1000)}ms")

@bot.command()
async def yardim(ctx):
    help_text = """
**Komutlar:**
`!selam` - Selam verir
`!ping` - Bot gecikmesini gosterir
`!yardim` - Bu mesaji gosterir
    """
    await ctx.send(help_text)

# BOTU BASLAT
bot.run(os.environ['DISCORD_TOKEN'])
