import discord
from discord.ext import commands
from discord import app_commands
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
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

BASVURU_KANAL_ID = 1524879141793435689
PAZAR_KANAL_ID = 1524866586912227330
SUPPORT_ROL_ID = 1524866585637031961

# YENI PAKET FIYATLARI
PAKETLER = {
    "demir": {"fiyat": 100, "kanal": "3 gun", "everyone": 1, "cekilis": False},
    "altin": {"fiyat": 200, "kanal": "5 gun", "greet": "3 gun", "everyone": 1, "cekilis": False},
    "elmas": {"fiyat": 300, "greet": "7 gun", "ozel_oda": True, "everyone": 1, "here": 1, "full_greet": True},
    "netherite": {"fiyat": 500, "kanal": "14 gun", "greet": "14 gun", "everyone": 2}
}

EK_OZELLIKLER = {
    "everyone": 80,
    "here": 40,
    "kanal_uzatma": 20
}

@bot.tree.command(name="selam", description="Selam verir")
async def slash_selam(interaction):
    await interaction.response.send_message(f"Selam {interaction.user.mention}!")

@bot.tree.command(name="ping", description="Bot gecikmesini gosterir")
async def slash_ping(interaction):
    await interaction.response.send_message(f"Pong! {round(bot.latency * 1000)}ms")

@bot.tree.command(name="paketler", description="Reklam paketlerini gosterir")
async def slash_paketler(interaction):
    embed = discord.Embed(title="💎 Reklam Paketleri", color=discord.Color.gold())
    embed.add_field(name="🔩 Demir Paket", value="100TL - 3 gunluk kanal + 1 everyone", inline=False)
    embed.add_field(name="🥇 Altin Paket", value="200TL - 5 gunluk kanal + 3 gunluk greet + 1 everyone", inline=False)
    embed.add_field(name="💎 Elmas Paket", value="300TL - 7 gun greet + ozel oda + 1 everyone + 1 here + full greet", inline=False)
    embed.add_field(name="⚔️ Netherite Paket", value="500TL - 14 gun kanal + 14 greet + 2 everyone", inline=False)
    embed.add_field(name="➕ Ek Ozellikler", value="1 everyone: 80TL | 1 here: 40TL | Kanal uzatma: 20TL", inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="reklam-fiyat-ayarla", description="Reklam paket fiyatlarini ayarlar (Yetkili)")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(paket="Paket adi (demir, altin, elmas, netherite)", fiyat="Yeni fiyat")
async def slash_reklam_fiyat_ayarla(interaction, paket: str, fiyat: int):
    paket = paket.lower()
    if paket not in PAKETLER:
        await interaction.response.send_message("Gecersiz paket!", ephemeral=True)
        return
    PAKETLER[paket]["fiyat"] = fiyat
    await interaction.response.send_message(f"{paket.capitalize()} Paket fiyati {fiyat}TL olarak guncellendi!", ephemeral=True)

@bot.tree.command(name="destek-panel", description="Destek paneli olusturur (Yetkili)")
@app_commands.checks.has_permissions(administrator=True)
async def slash_destek_panel(interaction):
    embed = discord
    
