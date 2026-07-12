import discord
import os
import random
import asyncio
import re
import time
from discord import app_commands
from discord.ui import Select, Modal, TextInput, View
from discord.ext import commands
from threading import Thread
from flask import Flask

# === AYARLAR VE KANAL ID'LERİ ===
BAŞVURU_LOG_KANAL_ID = 1524879141793435689
GIRIS_CIKIS_KANAL_ID = 123456789012345678
# --- BURAYI KENDİ REKLAM KANAL ID'N İLE DEĞİŞTİR ---
REKLAM_KANAL_ID = 112233445566778899 

# ... (Kalan kısımlar aynı) ...

# ⚡ GÜNCEL /greet KOMUTU (10 Saniye Sonra Silinir)
@bot.tree.command(name="greet", description="Reklam duyurusu atar ve 10sn sonra siler.")
@app_commands.checks.has_permissions(manage_messages=True)
@app_commands.describe(
    aciklama="Reklam açıklaması",
    etiket_gitsin_mi="True/False",
    link="İsteğe bağlı link"
)
async def slash_greet(interaction: discord.Interaction, aciklama: str, etiket_gitsin_mi: bool, link: str = None):
    hedef_kanal = interaction.guild.get_channel(REKLAM_KANAL_ID)
    
    if not hedef_kanal:
        await interaction.response.send_message("❌ **HATA:** Reklam kanalı bulunamadı! Kodun en üstündeki `REKLAM_KANAL_ID` kısmını gerçek kanal ID'n ile değiştirdiğinden emin ol.", ephemeral=True)
        return

    # Reklam metni
    greet_yazisi = f"**🌟 YENİ BİR PARTNER / REKLAM!**\n\n📌 **Açıklama:** {aciklama}"
    if link: greet_yazisi += f"\n🔗 **Katılmak İçin:** {link}"
    greet_yazisi += f"\n\n*Sunucumuza destekleri için teşekkür ederiz!*"
    if etiket_gitsin_mi: greet_yazisi += "\n@everyone"

    # Mesajı gönder
    msg = await hedef_kanal.send(content=greet_yazisi)
    await interaction.response.send_message(f"✅ Reklam <#{REKLAM_KANAL_ID}> kanalına gönderildi, 10 saniye sonra silinecek.", ephemeral=True)
    
    # 10 saniye bekle ve sil
    await asyncio.sleep(10)
    try:
        await msg.delete()
    except:
        pass # Mesaj zaten silinmişse hata vermez

# ... (Çekiliş, Destek ve diğer tüm komutlar buraya dahil) ...

# === BOT ON_READY ===
@bot.event
async def on_ready():
    # ... (Diğer view eklemeleri) ...
    await bot.tree.sync()
    print("--- Tüm Sistemler Aktif! ---")

keep_alive()
bot.run(os.environ.get("DISCORD_TOKEN"))
