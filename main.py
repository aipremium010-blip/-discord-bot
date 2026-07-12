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
REKLAM_KANAL_ID = 112233445566778899

# === RENDER KEEPALIVE SİSTEMİ ===
app = Flask('')

@app.route('/')
def home():
    return "MTTS Bot Aktif!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web)
    t.start()

# === BOT AYARLARI ===
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# === SÜRE DÖNÜŞTÜRÜCÜ FONKSİYON ===
def parse_duration(duration_str: str) -> int:
    match = re.match(r"(\d+)([smhd]?)", duration_str.lower().strip())
    if not match: return 0
    amount = int(match.group(1))
    unit = match.group(2)
    if unit == 's': return amount
    elif unit == 'm': return amount * 60
    elif unit == 'h': return amount * 3600
    elif unit == 'd': return amount * 86400
    else: return amount

# === BUTONLU ÇEKİLİŞ VIEW ===
class CekilisButonView(View):
    def __init__(self, odul: str, bitis_timestamp: int, kazanan_sayisi: int):
        super().__init__(timeout=None)
        self.odul = odul
        self.bitis_timestamp = bitis_timestamp
        self.kazanan_sayisi = kazanan_sayisi
        self.katilimcilar = set()

    @discord.ui.button(emoji="🎉", style=discord.ButtonStyle.primary, custom_id="cekilis_katil_butonu")
    async def katil_butonu(self, interaction: discord.Interaction, button: discord.Button):
        if int(time.time()) >= self.bitis_timestamp:
            await interaction.response.send_message("❌ Bu çekiliş çoktan sona erdi!", ephemeral=True)
            return
        user_id = interaction.user.id
        if user_id in self.katilimcilar:
            self.katilimcilar.remove(user_id)
            await interaction.response.send_message("👋 Çekilişten ayrıldınız.", ephemeral=True)
        else:
            self.katilimcilar.add(user_id)
            await interaction.response.send_message("🎉 Çekilişe katıldınız!", ephemeral=True)
        
        embed = interaction.message.embeds[0]
        embed.description = f"Katılmak için aşağıdaki *Butona* tıklayın!\n\n• Süre: <t:{self.bitis_timestamp}:R>\n• Kazanan Sayısı: {self.kazanan_sayisi}\n• Katılımcı Sayısı: {len(self.katilimcilar)}"
        await interaction.message.edit(embed=embed, view=self)

# === 1. DESTEK SİSTEMİ ===
class DestekKanalIciView(View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Kapat", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="ticket_kapat_btn_yeni")
    async def ticket_kapat(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.defer()
        await interaction.channel.send("🔒 Destek talebi 5 saniye içinde kapatılıyor...")
        await asyncio.sleep(5)
        await interaction.channel.delete()

# === 2. GÜNCEL REKLAM VE PİNG SİSTEMLERİ ===
class GreetMetniButon(discord.ui.Button):
    def __init__(self, link, aciklama):
        super().__init__(label="Greet Yazısını Al", style=discord.ButtonStyle.secondary, emoji="📋")
        self.link = link
        self.aciklama = aciklama
    async def callback(self, inter: discord.Interaction):
        greet_text = f"**🌟 YENİ BİR PARTNER / REKLAM!**\n\n📌 **Açıklama:** {self.aciklama}\n🔗 **Katılmak İçin:** {self.link}\n\n*Sunucumuza destekleri için teşekkür ederiz! @everyone*"
        await inter.response.send_message(f"```\n{greet_text}\n```\nKodu kopyalayıp reklam odasına atabilirsiniz.", ephemeral=True)

class ReklamHizmetModal(Modal):
    def __init__(self, hizmet_turu: str, detaylar: str = ""):
        super().__init__(title=f"{hizmet_turu} Başvuru Formu")
        self.hizmet_turu = hizmet_turu
        self.ad = TextInput(label="İsminiz", required=True)
        self.paket_secimi = TextInput(label="Seçtiğiniz Paket", default=detaylar, required=True)
        self.Detay = TextInput(label="Sunucu Detay", style=discord.TextStyle.paragraph, required=True)
        self.link = TextInput(label="Link", required=True)
        self.add_item(self.ad); self.add_item(self.paket_secimi); self.add_item(self.Detay); self.add_item(self.link)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        log_kanali = interaction.guild.get_channel(BAŞVURU_LOG_KANAL_ID)
        if log_kanali:
            embed = discord.Embed(title="📢 Yeni Reklam Başvurusu!", color=discord.Color.green())
            embed.add_field(name="Kullanıcı", value=interaction.user.mention, inline=True)
            embed.add_field(name="Hizmet", value=self.hizmet_turu, inline=True)
            embed.add_field(name="Link", value=self.link.value, inline=False)
            embed.add_field(name="Açıklama", value=self.Detay.value, inline=False)
            view = View()
            view.add_item(GreetMetniButon(link=self.link.value, aciklama=self.Detay.value))
            await log_kanali.send(embed=embed, view=view)
        await interaction.followup.send("✅ Başvurunuz iletildi!", ephemeral=True)

# === 3. SLASH KOMUTLARI ===

@bot.tree.command(name="greet", description="Reklam duyurusu atar.")
@app_commands.checks.has_permissions(manage_messages=True)
@app_commands.describe(aciklama="Reklam açıklaması", etiket_gitsin_mi="True/False", link="İsteğe bağlı link")
async def slash_greet(interaction: discord.Interaction, aciklama: str, etiket_gitsin_mi: bool, link: str = None):
    hedef_kanal = interaction.guild.get_channel(REKLAM_KANAL_ID)
    if not hedef_kanal:
        await interaction.response.send_message("❌ Reklam kanalı bulunamadı!", ephemeral=True)
        return
    greet_yazisi = f"**🌟 YENİ BİR PARTNER / REKLAM!**\n\n📌 **Açıklama:** {aciklama}"
    if link: greet_yazisi += f"\n🔗 **Katılmak İçin:** {link}"
    greet_yazisi += f"\n\n*Sunucumuza destekleri için teşekkür ederiz!*"
    if etiket_gitsin_mi: greet_yazisi += "\n@everyone"
    await hedef_kanal.send(content=greet_yazisi)
    await interaction.response.send_message("✅ Reklam gönderildi!", ephemeral=True)

@bot.tree.command(name="cekilis", description="Butonlu lüks çekiliş.")
@app_commands.checks.has_permissions(manage_messages=True)
async def slash_cekilis(interaction: discord.Interaction, sure: str, odul: str, kazanan_sayisi: int = 1):
    saniye = parse_duration(sure)
    bitis_timestamp = int(time.time()) + saniye
    embed = discord.Embed(title=f"🎁 {odul} Çekilişi", description=f"Katılmak için Butona tıklayın!\n\n• Süre: <t:{bitis_timestamp}:R>\n• Kazanan: {kazanan_sayisi}\n• Katılımcı: 0", color=discord.Color.green())
    await interaction.response.send_message("Çekiliş kuruluyor...", ephemeral=True)
    view = CekilisButonView(odul=odul, bitis_timestamp=bitis_timestamp, kazanan_sayisi=kazanan_sayisi)
    msg = await interaction.channel.send(embed=embed, view=view)
    await asyncio.sleep(saniye)
    for item in view.children: item.disabled = True
    await msg.edit(view=view)
    await interaction.channel.send("🎉 Çekiliş bitti!")

# === ON_READY ===
@bot.event
async def on_ready():
    await bot.tree.sync()
    print("--- MTTS Bot Aktif ve Çalışıyor ---")

keep_alive()
bot.run(os.environ.get("DISCORD_TOKEN"))
