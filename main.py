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

# === AYARLAR ===
BAŞVURU_LOG_KANAL_ID = 1524879141793435689

# === KEEPALIVE ===
app = Flask('')
@app.route('/')
def home(): return "MTTS Bot Aktif!"
def run_web(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
def keep_alive(): Thread(target=run_web).start()

# === BOT TANIMLAMASI ===
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# === YARDIMCI FONKSİYONLAR ===
def parse_duration(duration_str: str) -> int:
    match = re.match(r"(\d+)([smhd]?)", duration_str.lower().strip())
    if not match: return 0
    amount = int(match.group(1))
    unit = match.group(2)
    if unit == 's': return amount
    elif unit == 'm': return amount * 60
    elif unit == 'h': return amount * 3600
    elif unit == 'd': return amount * 86400
    return amount

# === VIEW SINIFLARI ===
class DestekKanalIciView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Kapat", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="ticket_kapat_btn_yeni")
    async def kapat(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.defer()
        await interaction.channel.delete()

class CekilisButonView(View):
    def __init__(self, odul, bitis, kazanan):
        super().__init__(timeout=None)
        self.odul, self.bitis, self.kazanan = odul, bitis, kazanan
        self.katilimcilar = set()
    @discord.ui.button(emoji="🎉", style=discord.ButtonStyle.primary, custom_id="cekilis_katil_butonu")
    async def katil(self, interaction: discord.Interaction, button: discord.Button):
        if int(time.time()) >= self.bitis:
            await interaction.response.send_message("❌ Süre doldu!", ephemeral=True)
            return
        if interaction.user.id in self.katilimcilar:
            self.katilimcilar.remove(interaction.user.id)
            await interaction.response.send_message("👋 Çekilişten ayrıldınız.", ephemeral=True)
        else:
            self.katilimcilar.add(interaction.user.id)
            await interaction.response.send_message("🎉 Katıldınız!", ephemeral=True)

# === KOMUTLAR ===

# 1. /greet (Kanal ID'siz, Bulunduğun kanala atar, 10sn sonra siler)
@bot.tree.command(name="greet", description="Bulunduğun kanala reklam atar ve 10sn sonra siler.")
@app_commands.checks.has_permissions(manage_messages=True)
async def slash_greet(interaction: discord.Interaction, aciklama: str, etiket_gitsin_mi: bool, link: str = None):
    greet_yazisi = f"**🌟 YENİ BİR PARTNER / REKLAM!**\n\n📌 **Açıklama:** {aciklama}"
    if link: greet_yazisi += f"\n🔗 **Link:** {link}"
    greet_yazisi += f"\n\n*Sunucumuza destekleri için teşekkür ederiz!*"
    if etiket_gitsin_mi: greet_yazisi += "\n@everyone"
    
    msg = await interaction.channel.send(content=greet_yazisi)
    await interaction.response.send_message("✅ Reklam gönderildi, 10sn sonra silinecek.", ephemeral=True)
    await asyncio.sleep(10)
    try: await msg.delete()
    except: pass

# 2. ÇEKİLİŞ
@bot.tree.command(name="cekilis", description="Butonlu çekiliş başlatır.")
@app_commands.checks.has_permissions(manage_messages=True)
async def slash_cekilis(interaction: discord.Interaction, sure: str, odul: str, kazanan_sayisi: int = 1):
    saniye = parse_duration(sure)
    bitis = int(time.time()) + saniye
    await interaction.response.send_message("Çekiliş kuruluyor...", ephemeral=True)
    view = CekilisButonView(odul, bitis, kazanan_sayisi)
    msg = await interaction.channel.send(f"🎁 **{odul}** Çekilişi Başladı!", view=view)
    await asyncio.sleep(saniye)
    for item in view.children: item.disabled = True
    await msg.edit(view=view)
    await interaction.channel.send("🎉 Çekiliş bitti!")

# 3. KANAL KONTROL
@bot.tree.command(name="lock", description="Kanalı kilitle.")
@app_commands.checks.has_permissions(manage_channels=True)
async def slash_lock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message("🔒 Kanal kilitlendi.", ephemeral=True)

@bot.tree.command(name="unlock", description="Kanal kilidini aç.")
@app_commands.checks.has_permissions(manage_channels=True)
async def slash_unlock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
    await interaction.response.send_message("🔓 Kanal kilidi açıldı.", ephemeral=True)

@bot.tree.command(name="sil", description="Mesaj siler.")
@app_commands.checks.has_permissions(administrator=True)
async def slash_sil(interaction: discord.Interaction, miktar: int):
    await interaction.response.defer(ephemeral=True)
    silinen = await interaction.channel.purge(limit=miktar)
    await interaction.followup.send(f"✅ {len(silinen)} mesaj silindi.", ephemeral=True)

# === BAŞLATMA ===
@bot.event
async def on_ready():
    bot.add_view(DestekKanalIciView())
    await bot.tree.sync()
    print("--- Tüm sistemler entegre edildi ve bot hazır! ---")

keep_alive()
bot.run(os.environ.get("DISCORD_TOKEN"))
