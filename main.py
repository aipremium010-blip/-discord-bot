import discord
from discord.ext import commands, tasks
from discord.ui import View, Button, Select, Modal, TextInput
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
def home(): return f"Bot aktif! Son kontrol: {datetime.now().strftime('%H:%M:%S')}"
@app.route('/ping')
def ping(): return "pong"
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

# === TÜM CLASS YAPILARI (Senin gönderdiğin uzun kodun kendisi) ===
class PaketDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Ping Hizmetleri", value="ping_hizmet", emoji="📢", description="Anlık everyone ve here etiket fiyatları."),
            discord.SelectOption(label="Özel Odalar & Kategori", value="oda_hizmet", emoji="🛠️", description="Özel kategori alanı ve karşılama sistemi.")
        ]
        super().__init__(placeholder="🔻 Paket Seçin:", min_values=1, max_values=1, options=options, custom_id="paket_ana_dropdown")
    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "ping_hizmet":
            embed = discord.Embed(title="📢 PING HİZMETLERİ", color=discord.Color.from_rgb(230, 126, 34))
            embed.description = "🔵 **Anlık `@everyone` Ping:** `80 TL`\n🟡 **Anlık `@here` Ping:** `50 TL`"
            await interaction.response.send_message(embed=embed, ephemeral=True)
        elif self.values[0] == "oda_hizmet":
            embed = discord.Embed(title="🛠️ ODA HİZMETLERİ", color=discord.Color.from_rgb(46, 204, 113))
            embed.description = "📂 **Özel Kategori Alanı:** `80 TL`\n👋 **Greet Karşılama Sistemi:** `80 TL`"
            await interaction.response.send_message(embed=embed, ephemeral=True)

class PaketPanelView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(PaketDropdown())

# ... (Buraya RolKararView, RolBasvuruView, YetkiliBasvuruView, PanelAnaView, TicketIciAksiyonView gibi diğer tüm sınıflarını ekle) ...

# === SLASH KOMUTLARI (Birleştirilmiş) ===

@bot.tree.command(name="paketler", description="Hizmet Paketleri panelini kurar.")
@app_commands.checks.has_permissions(administrator=True)
async def slash_paketler(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    embed = discord.Embed(title="💎 Hizmet Paketleri", description="Hizmetlerimizi inceleyin.", color=discord.Color.blue())
    if BANNER_URL: embed.set_image(url=BANNER_URL)
    await interaction.channel.send(embed=embed, view=PaketPanelView())
    await interaction.followup.send("✅ Paket paneli kuruldu.", ephemeral=True)

@bot.tree.command(name="destek-panel", description="Destek panelini oluşturur (Yönetici).")
@app_commands.checks.has_permissions(administrator=True)
async def slash_destek_panel(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    embed = discord.Embed(title="📥 Destek Menüsü", description="Lütfen destek almak istediğiniz kategoriyi seçin.", color=discord.Color.from_rgb(88, 101, 242))
    if BANNER_URL: embed.set_image(url=BANNER_URL)
    await interaction.channel.send(embed=embed, view=PanelAnaView())
    await interaction.followup.send("✅ Destek paneli kuruldu.", ephemeral=True)

@bot.tree.command(name="sil", description="Belirtilen miktarda mesajı siler.")
@app_commands.checks.has_permissions(administrator=True)
async def slash_sil(interaction: discord.Interaction, miktar: int):
    await interaction.response.defer(ephemeral=True)
    silinen = await interaction.channel.purge(limit=miktar)
    await interaction.followup.send(f"✅ {len(silinen)} mesaj silindi.", ephemeral=True)

# === ON_READY VE BAŞLATMA ===

@bot.event
async def on_ready():
    # Tüm view sınıflarını kaydet
    bot.add_view(PaketPanelView())
    bot.add_view(PanelAnaView())
    bot.add_view(RolBasvuruView())
    bot.add_view(YetkiliBasvuruView())
    
    await bot.tree.sync()
    print(f"--- {bot.user} başarıyla başlatıldı ve senkronize edildi! ---")

bot.run("TOKEN_BURAYA")
