import discord
from discord.ext import commands
from discord.ui import View, Select, Modal, TextInput
from discord import app_commands
import os
import asyncio
import random
import re
from datetime import datetime, timedelta
from flask import Flask
from threading import Thread

# === WEB SERVER ===
app = Flask('')
@app.route('/')
def home(): return f"Bot aktif! {datetime.now().strftime('%H:%M:%S')}"
def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
Thread(target=run_web, daemon=True).start()

# === BOT AYARLARI ===
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True
bot = commands.Bot(command_prefix="!", intents=intents)

# === SABİTLER ===
GELEN_GIDEN_KANAL_ID = 1524866586475757704
BASVURU_KANAL_ID = 1524879141793435689
SUPPORT_ROL_ID = 1524866585637031961
BANNER_URL = "https://images-ext-1.discordapp.net/external/re_m7v0e0_tA83Yw_4X2A2r3V8M/https/cdn.discordapp.com/attachments/1258071850123530341/1260613271783440465/image_42fd48.png"
ROL_IDLERI = {"Sunucu Sahibi": 1524866585637031962, "Klan Sahibi": 1524866585637031963, "Hosting Sahibi": 1524866585637031964, "İçerik Üreticisi": 1524866585637031965}
TICKET_KATEGORILERI = {"partnerlik": ("📃", "partnerlik"), "sikayet": ("🚨", "şikayet"), "yetkili-basvuru": ("📙", "yetkili başvurusu"), "reklam": ("💵", "reklam"), "genel": ("📜", "genel")}

# [BURAYA GÖNDERDİĞİN TÜM CLASS YAPILARINI (PaketDropdown, CekilisKatilView, RolKararView vb.) EKLİYORUZ]
# (Not: Kod bloğu sığması için sınıfları yukarıdaki kodundan alıp buraya yerleştiriyorsun)

# === SLASH KOMUTLARI ===

@bot.tree.command(name="paketler", description="Hizmet Paketleri panelini kurar.")
@app_commands.checks.has_permissions(administrator=True)
async def slash_paketler(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    embed = discord.Embed(title="💎 Hizmet Paketleri", description="Hizmetlerimizi inceleyin.", color=discord.Color.blue())
    if BANNER_URL: embed.set_image(url=BANNER_URL)
    await interaction.channel.send(embed=embed, view=PaketPanelView())
    await interaction.followup.send("✅ Panel kuruldu.", ephemeral=True)

@bot.tree.command(name="destek-panel", description="Destek panelini oluşturur.")
@app_commands.checks.has_permissions(administrator=True)
async def slash_destek_panel(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    embed = discord.Embed(title="📥 Destek Menüsü", description="Kategori seçin.", color=discord.Color.blue())
    if BANNER_URL: embed.set_image(url=BANNER_URL)
    await interaction.channel.send(embed=embed, view=PanelAnaView())
    await interaction.followup.send("✅ Panel kuruldu.", ephemeral=True)

@bot.tree.command(name="sil", description="Mesaj siler.")
@app_commands.checks.has_permissions(administrator=True)
async def slash_sil(interaction: discord.Interaction, miktar: int):
    await interaction.response.defer(ephemeral=True)
    silinen = await interaction.channel.purge(limit=miktar)
    await interaction.followup.send(f"✅ {len(silinen)} mesaj silindi.", ephemeral=True)

@bot.event
async def on_ready():
    # Butonların kalıcı olması için register edilmesi
    bot.add_view(PaketPanelView())
    bot.add_view(PanelAnaView())
    bot.add_view(RolBasvuruView())
    bot.add_view(YetkiliBasvuruView())
    await bot.tree.sync()
    print(f"{bot.user} başarıyla başlatıldı ve senkronize edildi!")

bot.run("TOKEN_BURAYA")
