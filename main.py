import discord
from discord.ext import commands, tasks
from discord.ui import View, Button, Select, Modal, TextInput
from discord import app_commands
import os
import asyncio
import random
from datetime import datetime, timedelta
from flask import Flask
from threading import Thread
import urllib.request

# === WEB SERVER ===
app = Flask('')
@app.route('/')
def home(): return f"Bot aktif! {datetime.now().strftime('%H:%M:%S')}"
@app.route('/ping')
def ping(): return "pong"
def run_web(): app.run(host='0.0.0.0', port=8080)
Thread(target=run_web, daemon=True).start()

# === BOT AYARLARI ===
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True
bot = commands.Bot(command_prefix="!", intents=intents)

# === ID YAPILANDIRMALARI ===
GELEN_GIDEN_KANAL_ID = 1524879141793435689
BASVURU_KANAL_ID = 1524879141793435689
LOG_KANAL_ID = 1524879141793435689
PAZAR_KANAL_ID = 1524866586912227330
SUPPORT_ROL_ID = 1524866585637031961

# === MTTS GÖRSEL LOGO URL (1024x1024) ===
# Sağ taraftaki küçük kare (thumbnail) ve alt bannerlar için ortak kullanılacak ana görsel linkin:
BANNER_URL = "https://images-ext-1.discordapp.net/external/re_m7v0e0_tA83Yw_4X2A2r3V8M/https/cdn.discordapp.com/attachments/..." 

ROL_IDLERI = {
    "Sunucu Sahibi": 1524866585637031962,   
    "Klan Sahibi": 1524866585637031963,
    "Hosting Sahibi": 1524866585637031964,
    "İçerik Üreticisi": 1524866585637031965
}

TICKET_KATEGORILERI = {
    "partnerlik": ("📃", "partnerlik"),
    "sikayet": ("🚨", "şikayet"),
    "yetkili-basvuru": ("📙", "yetkili başvurusu"),
    "reklam": ("💵", "reklam"),
    "genel": ("📜", "genel")
}

# === TICKET ODASI İÇİ BUTONLARI VE HAREKETLERİ ===
class TicketIciAksiyonView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Kapat", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="ticket_kapat_btn")
    async def kapat(self, interaction: discord.Interaction, button: discord.Button):
        support_rol = interaction.guild.get_role(SUPPORT_ROL_ID)
        if interaction.user.guild_permissions.administrator or (support_rol and support_rol in interaction.user.roles):
            await interaction.response.send_message("⚙️ Destek talebi 5 saniye içerisinde kalıcı olarak kapatılıyor...")
            await asyncio.sleep(5)
            await interaction.channel.delete()
        else:
            await interaction.response.send_message("❌ Bu işlem için yetkiniz bulunmuyor!", ephemeral=True)

    @discord.ui.button(label="Aktif Yetkililer", style=discord.ButtonStyle.primary, emoji="👤", custom_id="ticket_yetkililer_btn")
    async def yetkililer(self, interaction: discord.Interaction, button: discord.Button):
        support_rol = interaction.guild.get_role(SUPPORT_ROL_ID)
        embed = discord.Embed(title="🛡️ Aktif Destek Ekibi", color=discord.Color.blue())
        if support_rol:
            aktifler = [m.mention for m in support_rol.members if m.status != discord.Status.offline]
            embed.description = "Şu an çevrimiçi olan yetkililer:\n" + ", ".join(aktifler) if aktifler else "Şu an aktif yetkili bulunmuyor."
        else:
            embed.description = "Destek rolü sunucuda bulunamadı."
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Yardım Al", style=discord.ButtonStyle.success, emoji="🆘", custom_id="ticket_yardim_btn")
    async def yardim_al(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.send_message("🛎️ Destek ekibine acil durum bildirimi geçildi. En kısa sürede yanıt alacaksınız.", ephemeral=True)

# === TICKET MODAL VERI GIRISI ===
class DestekGirisModal(Modal, title="Destek Talebi Formu"):
    konu = TextInput(label="Talep Konusu / Gerekçeniz", placeholder="Örn: Partnerlik isteği", required=True)

    def __init__(self, kategori_key):
        super().__init__()
        self.kategori_key = kategori_key

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        user = interaction.user
        emoji, kategori_adi = TICKET_KATEGORILERI[self.kategori_key]
        
        support_rol = guild.get_role(SUPPORT_ROL_ID)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        if support_rol:
            overwrites[support_rol] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        channel = await guild.create_text_channel(name=f"ticket-{user.name}", overwrites=overwrites)
        
        suan = datetime.now()
        tarih_str = suan.strftime("%d %B %Y %H:%M")
        ticket_id = random.randint(1000000000, 9999999999)

        embed = discord.Embed(color=discord.Color.from_rgb(88, 101, 242))
        embed.set_author(name="📑 Destek Talebi")
        embed.description = "Destek ekibimiz en kısa sürede size yardımcı olacaktır.\n\n" \
                            f"📌 **Konu**\n{self.konu.value}\n\n" \
                            f"📂 **Kategori**\n{kategori_adi} \n\n" \
                            f"👤 **Kullanıcı**\n{user.name}\n\n" \
                            f"🆔 **Kullanıcı ID**\n{user.id}\n\n" \
                            f"⏱️ **Açılış Zamanı**\n{tarih_str}"
        
        embed.set_thumbnail(url=user.display_avatar.url) # Bilet içinde açan kişinin profil resmi sağda kalmaya devam eder
        embed.set_footer(text=f"Ticket ID: {ticket_id} • bugün saat {suan.strftime('%H:%M')}")

        if support_rol:
            await channel.send(content=f"{user.mention}, destek talebiniz açıldı. {support_rol.mention}", embed=embed, view=TicketIciAksiyonView())
        else:
            await channel.send(content=f"{user.mention}, destek talebiniz açıldı.", embed=embed, view=TicketIciAksiyonView())
            
        await interaction.followup.send(f"✅ Destek odanız başarıyla oluşturuldu: {channel.mention}", ephemeral=True)

# === DIŞ GÖRÜNÜM MENÜSÜ VE PANELİ ===
class PanelKategoriDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Partnerlik", value="partnerlik", emoji="📃"),
            discord.SelectOption(label="Şikayet", value="sikayet", emoji="🚨"),
            discord.SelectOption(label="Yetkili Başvurusu", value="yetkili-basvuru", emoji="📙"),
            discord.SelectOption(label="Reklam", value="reklam", emoji="💵"),
            discord.SelectOption(label="Genel", value="genel", emoji="📜")
        ]
        super().__init__(placeholder="📌 Bir destek kategorisi seçin", min_values=1, max_values=1, custom_id="panel_dropdown")

    async def callback(self, interaction: discord.Interaction):
        kategori_key = self.values[0]
        await interaction.response.send_modal(DestekGirisModal(kategori_key))

class PanelAnaView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(PanelKategoriDropdown())

# =====================================================================
# === KOMUTLAR VE TETİKLEYİCİLER ===
# =====================================================================

@bot.tree.command(name="destek-panel", description="Dış destek panelini MTTS logosuyla oluşturur (Yönetici).")
@app_commands.checks.has_permissions(administrator=True)
async def slash_destek_panel(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📥 Destek Menüsü",
        description="Aşağıdaki menüden destek talebi açabilirsiniz.\n\n"
                    "**• Yetkilileri meşgul etmek yasaktır.**\n"
                    "**• Destek taleplerinizi kategorilere göre açın.**\n"
                    "**• Uygun kanal seçildikten sonra destek ekibi bilgilendirilecektir.**\n\n"
                    "Bir kategori seçerek destek talebi açabilirsiniz. • " + datetime.now().strftime("%d.%m.%Y %H:%M"),
        color=discord.Color.from_rgb(88, 101, 242)
    )
    
    # Kılıç yerine sağ taraftaki küçük kare kutucuğa doğrudan MTTS logosunu çeker:
    if BANNER_URL:
        embed.set_thumbnail(url=BANNER_URL)
    
    await interaction.response.send_message("Panel başarıyla kuruldu.", ephemeral=True)
    await interaction.channel.send(embed=embed, view=PanelAnaView())

# Standart Diğer Komut Yapıları
@bot.tree.command(name="selam", description="Sunucudakilere selam verir.")
async def slash_selam(interaction: discord.Interaction):
    await interaction.response.send_message(f"Selam {interaction.user.mention}! Hoş geldin. 👋")

@bot.tree.command(name="ping", description="Botun anlık gecikme süresini gösterir.")
async def slash_ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"🏓 Pong! Gecikme: `{round(bot.latency * 1000)}ms`")

@bot.tree.command(name="sil", description="Mesajları temizler (Yönetici).")
@app_commands.checks.has_permissions(administrator=True)
async def slash_sil(interaction: discord.Interaction, miktar: int):
    await interaction.response.defer(ephemeral=True)
    await interaction.channel.purge(limit=miktar)
    await interaction.followup.send("🗑️ Temizlendi.", ephemeral=True)

# === KESİN ÇALIŞAN GELEN - GİDEN SİSTEMİ ===
@bot.event
async def on_member_join(member):
    channel = member.guild.get_channel(GELEN_GIDEN_KANAL_ID)
    if channel:
        embed = discord.Embed(
            title="📥 Biri Aramıza Katıldı!",
            description=f"{member.mention} sunucumuza hoş geldin! Seninle birlikte **{len(member.guild.members)}** kişi olduk. 🎉", 
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        if BANNER_URL: embed.set_image(url=BANNER_URL)
        await channel.send(content=f"Hoş geldin {member.mention}!", embed=embed)

@bot.event
async def on_member_remove(member):
    channel = member.guild.get_channel(GELEN_GIDEN_KANAL_ID)
    if channel:
        embed = discord.Embed(
            title="📤 Biri Aramızdan Ayrıldı...",
            description=f"{member.mention} sunucudan ayrıldı. Görüşmek üzere! Geride **{len(member.guild.members)}** kişi kaldık. 😢", 
            color=discord.Color.red()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        if BANNER_URL: embed.set_image(url=BANNER_URL)
        await channel.send(content=f"**{member.name}** sunucudan ayrıldı.", embed=embed)

@tasks.loop(seconds=30)
async def keep_alive_loop():
    try:
        req = urllib.request.Request("http://localhost:8080/ping", method="GET")
        with urllib.request.urlopen(req, timeout=5) as r: pass
    except: pass

@bot.event
async def on_ready():
    print(f"Bot sorunsuzca başlatıldı: {bot.user}")
    try:
        for guild in bot.guilds: await bot.tree.sync(guild=guild)
        print("Tüm sistem senkronize edildi!")
    except Exception as e: print(e)
    if not keep_alive_loop.is_running(): keep_alive_loop.start()

TOKEN = os.environ.get('DISCORD_TOKEN', '')
if TOKEN: bot.run(TOKEN, reconnect=True)
