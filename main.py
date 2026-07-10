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

# === WEB SERVER (Render için keep-alive) ===
app = Flask('')

@app.route('/')
def home():
    return f"Bot aktif! Son ping: {datetime.now().strftime('%H:%M:%S')}"

@app.route('/ping')
def ping():
    return "pong"

def run_web():
    app.run(host='0.0.0.0', port=8080)

Thread(target=run_web, daemon=True).start()

# === BOT AYARLARI ===
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)

# === KANAL / ROL ID'LERİ ===
BASVURU_KANAL_ID = 1524879141793435689
LOG_KANAL_ID = 1524879141793435689
PAZAR_KANAL_ID = 1524866586912227330
SUPPORT_ROL_ID = 1524866585637031961

# === MTTS GÖRSEL LOGO URL (1024x1024 / Banner) ===
# NOT: Eğer bu link kırılırsa, yüklediğin yeni görselin linkini buraya yapıştırabilirsin.
BANNER_URL = "https://images-ext-1.discordapp.net/external/re_m7v0e0_tA83Yw_4X2A2r3V8M/https/cdn.discordapp.com/attachments/..." 

ROL_IDLERI = {
    "Sunucu Sahibi": 1524866585637031962,   
    "Klan Sahibi": 1524866585637031963,
    "Hosting Sahibi": 1524866585637031964,
    "İçerik Üreticisi": 1524866585637031965
}

# === TICKET KATEGORİLERİ ===
TICKET_KATEGORILERI = {
    "partnerlik": ("📃", "Partnerlik"),
    "sikayet": ("🚨", "Sikayet"),
    "yetkili-basvuru": ("📙", "Yetkili Basvurusu"),
    "reklam": ("💵", "Reklam"),
    "genel": ("📜", "Genel")
}

# === PAKET DETAYLARI ===
PAKET_DETAYLARI = {
    "demir": {"emoji": "🔩", "isim": "Demir Paket", "fiyat": 100, "renk": "#B0B0B0", "ozellikler": ["Temel reklam hizmetleri", "3 günlük kanal size ait", "Çekiliş sizden", "1 everyone hakkı"]},
    "altin": {"emoji": "🥇", "isim": "Altın Paket", "fiyat": 200, "renk": "#FFD700", "ozellikler": ["5 günlük reklam paketi", "Çekiliş bizden", "1 everyone hakkı"]},
    "elmas": {"emoji": "💎", "isim": "Elmas Paket", "fiyat": 300, "renk": "#00CED1", "ozellikler": ["7 günlük reklam paketi", "Çekiliş bizden", "1 everyone + 1 here hakkı"]},
    "netherite": {"emoji": "⚔️", "isim": "Netherite Paket", "fiyat": 400, "renk": "#4A0080", "ozellikler": ["14 günlük reklam paketi", "Reklam odası", "2 everyone + 1 here hakkı", "Çekiliş bizden"]}
}

aktif_cekilisler = {}

# === ÇEKİLİŞ SİSTEMİ ===
class CekilisKatilView(View):
    def __init__(self, cekilis_id):
        super().__init__(timeout=None)
        self.cekilis_id = cekilis_id

    @discord.ui.button(label="", style=discord.ButtonStyle.primary, emoji="🎉", custom_id="cekilis_katil_btn")
    async def katil(self, interaction: discord.Interaction, button: discord.Button):
        if self.cekilis_id not in aktif_cekilisler:
            await interaction.response.send_message("Bu çekiliş sona ermiş veya bulunamadı.", ephemeral=True)
            return
        katilimcilar = aktif_cekilisler[self.cekilis_id]["katilimcilar"]
        if interaction.user.id in katilimcilar:
            katilimcilar.remove(interaction.user.id)
            await interaction.response.send_message("Çekilişten katılımınızı çektiniz. ❌", ephemeral=True)
        else:
            katilimcilar.append(interaction.user.id)
            await interaction.response.send_message("Çekilişe başarıyla katıldınız! 🎉", ephemeral=True)
            
        embed = interaction.message.embeds[0]
        for idx, field in enumerate(embed.fields):
            if "Katılımcı Sayısı" in field.name:
                embed.set_field_at(idx, name="• Katılımcı Sayısı:", value=str(len(katilimcilar)), inline=False)
                break
        await interaction.message.edit(embed=embed)

# === BAŞVURU SİSTEMİ ===
class BasvuruOnayView(View):
    def __init__(self, basvuran_id: int, rol_adi: str):
        super().__init__(timeout=None)
        self.basvuran_id = basvuran_id
        self.rol_adi = rol_adi

    @discord.ui.button(label="Kabul Et", style=discord.ButtonStyle.success, custom_id="basvuru_onay")
    async def kabul_et(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        try: member = await guild.fetch_member(self.basvuran_id)
        except discord.NotFound:
            await interaction.followup.send("Başvuran kullanıcı sunucudan ayrılmış!", ephemeral=True)
            return

        rol_id = ROL_IDLERI.get(self.rol_adi)
        rol = guild.get_role(rol_id) if rol_id else None

        if member and rol:
            await member.add_role(rol)
            embed = interaction.message.embeds[0]
            for idx, field in enumerate(embed.fields):
                if field.name == "Durum":
                    embed.set_field_at(idx, name="Durum", value="✅ Kabul Edildi", inline=False)
                    break
            await interaction.message.edit(embed=embed, view=None)
            await interaction.followup.send(f"{member.mention} kullanıcısına {rol.name} rolü verildi.", ephemeral=True)
            try: await member.send(f"Tebrikler! **{self.rol_adi}** başvurunuz kabul edildi.")
            except: pass

    @discord.ui.button(label="Reddet", style=discord.ButtonStyle.danger, custom_id="basvuru_red")
    async def reddet(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.defer(ephemeral=True)
        try: member = await interaction.guild.fetch_member(self.basvuran_id)
        except discord.NotFound: member = None

        embed = interaction.message.embeds[0]
        for idx, field in enumerate(embed.fields):
            if field.name == "Durum":
                embed.set_field_at(idx, name="Durum", value="❌ Reddedildi", inline=False)
                break
        await interaction.message.edit(embed=embed, view=None)
        await interaction.followup.send("Başvuru reddedildi.", ephemeral=True)

class RolBasvuruModal(Modal, title="Rol Başvuru Formu"):
    proje_adi = TextInput(label="Projenizin/Sunucunuzun Adı", placeholder="Örn: MC-Türkiye", required=True)
    kanit_link = TextInput(label="Kanıt/Discord/Web Linki", placeholder="https://...", required=True)
    detaylar = TextInput(label="Eklemek İstediğiniz Detaylar", placeholder="Ek bilgiler...", required=False, style=discord.TextStyle.paragraph)

    def __init__(self, rol_adi):
        super().__init__()
        self.rol_adi = rol_adi

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"{self.rol_adi} başvurunuz alındı!", ephemeral=True)
        basvuru_kanal = interaction.guild.get_channel(BASVURU_KANAL_ID)
        if basvuru_kanal:
            embed = discord.Embed(title=f"{self.rol_adi} Başvurusu", color=discord.Color.gold())
            embed.add_field(name="Başvuran", value=interaction.user.mention, inline=False)
            embed.add_field(name="Rol", value=self.rol_adi, inline=False)
            embed.add_field(name="Proje Adı", value=self.proje_adi.value, inline=False)
            embed.add_field(name="Kanıt Linki", value=self.kanit_link.value, inline=False)
            embed.add_field(name="Durum", value="⏳ Onay Bekliyor", inline=False)
            await basvuru_kanal.send(embed=embed, view=BasvuruOnayView(interaction.user.id, self.rol_adi))

# === TICKET SİSTEMİ ===
class DestekModal(Modal, title="Destek Talebi"):
    konu = TextInput(label="Kısaca konunuzdan bahsedin", placeholder="Örn: Reklam almak istiyorum", required=True)

    def __init__(self, kategori_key):
        super().__init__()
        self.kategori_key = kategori_key
        self.emoji, self.kategori_adi = TICKET_KATEGORILERI[kategori_key]

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"**{self.emoji} {self.kategori_adi} Ticketi** açılıyor...", ephemeral=True)
        support_rol = interaction.guild.get_role(SUPPORT_ROL_ID)
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        if support_rol: overwrites[support_rol] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        channel = await interaction.guild.create_text_channel(name=f"ticket-{interaction.user.name}", overwrites=overwrites)
        embed = discord.Embed(title=f"{self.emoji} ACILIS SEBEBI: {self.kategori_adi.upper()}", description=f"**Kısaca Konunuz:** {self.konu.value}", color=discord.Color.green())
        
        # İstek Üzerine: Destek odasındaki bilgilendirme görseli
        if BANNER_URL:
            embed.set_image(url=BANNER_URL)
            
        if support_rol:
            await channel.send(f"{support_rol.mention} {interaction.user.mention} yeni destek talebi oluşturdu.", embed=embed)
        else:
            await channel.send(content=f"{interaction.user.mention} Destek talebiniz açıldı.", embed=embed)
        await channel.send(view=TicketKapatView())

class TicketKapatView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Talebi Kapat", style=discord.ButtonStyle.danger, emoji="🔒")
    async def kapat(self, interaction, button):
        support_rol = interaction.guild.get_role(SUPPORT_ROL_ID)
        if interaction.user.guild_permissions.administrator or (support_rol and support_rol in interaction.user.roles):
            await interaction.response.send_message("Ticket 5 saniye sonra kapatılacak...")
            await asyncio.sleep(5)
            await interaction.channel.delete()
        else:
            await interaction.response.send_message("Bu işlem için yetkiniz yok!", ephemeral=True)

class TicketKonuView(View):
    def __init__(self, kategori_key):
        super().__init__(timeout=None)
        self.kategori_key = kategori_key
    @discord.ui.button(label="Ticket Aç", style=discord.ButtonStyle.success, emoji="🎫")
    async def ticket_ac(self, interaction, button):
        await interaction.response.send_modal(DestekModal(self.kategori_key))

class DestekKategoriSecView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.select(
        placeholder="Lütfen kategori seçin...",
        options=[
            discord.SelectOption(label="Partnerlik", value="partnerlik", emoji="📃"),
            discord.SelectOption(label="Şikayet", value="sikayet", emoji="🚨"),
            discord.SelectOption(label="Yetkili Başvurusu", value="yetkili-basvuru", emoji="📙"),
            discord.SelectOption(label="Reklam", value="reklam", emoji="💵"),
            discord.SelectOption(label="Genel", value="genel", emoji="📜")
        ]
    )
    async def kategori_sec(self, interaction, select):
        kategori_key = select.values[0]
        emoji, kategori_adi = TICKET_KATEGORILERI[kategori_key]
        embed = discord.Embed(title=f"{emoji} {kategori_adi} Desteği", description="Destek talebi açmak için aşağıdaki butona tıklayın.", color=discord.Color.blurple())
        await interaction.response.send_message(embed=embed, view=TicketKonuView(kategori_key), ephemeral=True)

class DestekPanelView(View):
    def __init__(self): super().__init__(timeout=None)
    
    @discord.ui.button(label="Aktif Yetkililer", style=discord.ButtonStyle.primary, emoji="👑", custom_id="panel_yetkililer")
    async def aktif_yetkililer(self, interaction: discord.Interaction, button: discord.Button):
        support_rol = interaction.guild.get_role(SUPPORT_ROL_ID)
        embed = discord.Embed(title="🛡️ Aktif Yetkili Kadrosu", color=discord.Color.green())
        if support_rol:
            aktif_üyeler = [m.mention for m in support_rol.members if m.status != discord.Status.offline]
            embed.description = "Şu anda aktif olan yetkililerimiz:\n" + ", ".join(aktif_üyeler) if aktif_üyeler else f"Aktif yetkili bulunmuyor."
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Destek Al", style=discord.ButtonStyle.success, emoji="🎫", custom_id="panel_destek_al")
    async def destek_al(self, interaction: discord.Interaction, button: discord.Button):
        embed = discord.Embed(title="🎫 Destek Talebi Oluşturma", description="Lütfen menüden ilgili kategoriyi seçiniz.", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, view=DestekKategoriSecView(), ephemeral=True)

# === REKLAM PAKETLERİ VİEW ===
class PaketDetayView(View):
    def __init__(self, paket_key): super().__init__(timeout=None)
    @discord.ui.button(label="Geri Dön", style=discord.ButtonStyle.secondary, emoji="◀️")
    async def geri_don(self, interaction, button):
        embed = discord.Embed(title="MC Türkiye - Reklam Hizmetleri", color=discord.Color.gold())
        await interaction.response.edit_message(embed=embed, view=PaketlerView())

class PaketlerView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.select(
        placeholder="Bir paket seçiniz...",
        options=[
            discord.SelectOption(label="Demir Paket - 100TL", value="demir"),
            discord.SelectOption(label="Altın Paket - 200TL", value="altin"),
            discord.SelectOption(label="Elmas Paket - 300TL", value="elmas"),
            discord.SelectOption(label="Netherite Paket - 400TL", value="netherite")
        ]
    )
    async def paket_sec(self, interaction, select):
        paket_key = select.values[0]
        detay = PAKET_DETAYLARI[paket_key]
        embed = discord.Embed(title=f"{detay['emoji']} {detay['isim']}", description=f"**Fiyat:** {detay['fiyat']}TL", color=discord.Color(int(detay['renk'].replace('#', ''), 16)))
        embed.add_field(name="Özellikler", value="\n".join([f"- {oz}" for oz in detay['ozellikler']]), inline=False)
        await interaction.response.edit_message(embed=embed, view=PaketDetayView(paket_key))

class RolBasvuruView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Sunucu Sahibi", style=discord.ButtonStyle.primary, emoji="👑")
    async def ss(self, interaction, b): await interaction.response.send_modal(RolBasvuruModal("Sunucu Sahibi"))
    @discord.ui.button(label="Klan Sahibi", style=discord.ButtonStyle.primary, emoji="⚔️")
    async def ks(self, interaction, b): await interaction.response.send_modal(RolBasvuruModal("Klan Sahibi"))

# =====================================================================
# === 1. HERKESİN KULLANABİLECEĞİ KOMUTLAR ===
# =====================================================================

@bot.tree.command(name="selam", description="Sunucudakilere selam verir.")
async def slash_selam(interaction: discord.Interaction):
    await interaction.response.send_message(f"Selam {interaction.user.mention}! Hoş geldin. 👋")

@bot.tree.command(name="ping", description="Botun anlık gecikme süresini gösterir.")
async def slash_ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"🏓 Pong! Gecikme: `{round(bot.latency * 1000)}ms`")

@bot.tree.command(name="yardim", description="Tüm komutlar hakkında bilgi verir.")
async def slash_yardim(interaction: discord.Interaction):
    embed = discord.Embed(title="📜 MC Türkiye Bot Komut Listesi", color=discord.Color.blue())
    embed.add_field(name="👥 Herkesin Kullanabileceği Komutlar", value="`/selam`, `/ping`, `/yardim`, `/paketler`, `/ilan-ver`")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="paketler", description="Mevcut reklam paketlerini listeler.")
async def slash_paketler(interaction: discord.Interaction):
    embed = discord.Embed(title="MC Türkiye Topluluk Sunucusu - Reklam Hizmetleri", color=discord.Color.gold())
    await interaction.response.send_message(embed=embed, view=PaketlerView())

@bot.tree.command(name="ilan-ver", description="Pazar alanında otomatik ilan oluşturur.")
async def slash_ilan_ver(interaction: discord.Interaction, urun: str, fiyat: str, aciklama: str):
    pazar_channel = interaction.guild.get_channel(PAZAR_KANAL_ID)
    if not pazar_channel: return
    embed = discord.Embed(title="🛒 Yeni Ticaret İlanı", color=discord.Color.orange())
    embed.add_field(name="Ürün/Hizmet", value=urun, inline=True)
    embed.add_field(name="Fiyat", value=fiyat, inline=True)
    embed.add_field(name="Açıklama", value=aciklama, inline=False)
    msg = await pazar_channel.send(embed=embed)
    await msg.add_reaction("✅")
    await interaction.response.send_message("İlan gönderildi!", ephemeral=True)

# =====================================================================
# === 2. SADECE YÖNETİCİLERİN KULLANABİLECEĞİ KOMUTLAR ===
# =====================================================================

@bot.tree.command(name="cekilis-yap", description="Butonlu çekiliş başlatır (Yönetici).")
@app_commands.checks.has_permissions(administrator=True)
async def slash_cekilis(interaction: discord.Interaction, odul: str, sure_dakika: int, kazanan_sayisi: int):
    await interaction.response.send_message("Çekiliş başlatılıyor...", ephemeral=True)
    bitis_zamani = datetime.utcnow() + timedelta(minutes=sure_dakika)
    timestamp_format = f"<t:{int(bitis_zamani.timestamp())}:R>"
    
    embed = discord.Embed(title=f"🎁 {odul} Çekilişi - Başladı!", description="Katılmak için aşağıdaki **Butona** tıklayın!", color=discord.Color.green())
    embed.add_field(name="• Süre:", value=timestamp_format, inline=False)
    embed.add_field(name="• Kazanan Sayısı:", value=str(kazanan_sayisi), inline=False)
    embed.add_field(name="• Katılımcı Sayısı:", value="0", inline=False)
    
    msg = await interaction.channel.send(embed=embed)
    cekilis_id = msg.id
    aktif_cekilisler[cekilis_id] = {"katilimcilar": [], "odul": odul, "kazanan_sayisi": kazanan_sayisi, "aktif": True}
    await msg.edit(view=CekilisKatilView(cekilis_id))
    
    await asyncio.sleep(sure_dakika * 60)
    if cekilis_id in aktif_cekilisler:
        data = aktif_cekilisler[cekilis_id]
        if len(data["katilimcilar"]) > 0:
            kazananlar = random.sample(data["katilimcilar"], min(data["kazanan_sayisi"], len(data["katilimcilar"])))
            mentions = ", ".join([f"<@{k}>" for k in kazananlar])
            await interaction.channel.send(f"🎉 Tebrikler {mentions}! **{odul}** çekilişini kazandınız!")
        del aktif_cekilisler[cekilis_id]

@bot.tree.command(name="greet", description="Manuel test hoş geldin mesajı atar (Yönetici).")
@app_commands.checks.has_permissions(administrator=True)
async def slash_greet(interaction: discord.Interaction, uye: discord.Member):
    embed = discord.Embed(description=f"{uye.mention} aramıza katıldı! Hoş geldin! 🎉", color=discord.Color.green())
    embed.set_thumbnail(url=uye.display_avatar.url)
    if BANNER_URL: embed.set_image(url=BANNER_URL) # Greet komutuna eklenen görsel
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="lock", description="Kanalı kilitler (Yönetici).")
@app_commands.checks.has_permissions(administrator=True)
async def slash_lock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message("🔒 Kanal kilitlendi.", ephemeral=True)

@bot.tree.command(name="unlock", description="Kanal kilidini açar (Yönetici).")
@app_commands.checks.has_permissions(administrator=True)
async def slash_unlock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
    await interaction.response.send_message("🔓 Kanal açıldı.", ephemeral=True)

@bot.tree.command(name="sil", description="Mesajları temizler (Yönetici).")
@app_commands.checks.has_permissions(administrator=True)
async def slash_sil(interaction: discord.Interaction, miktar: int):
    await interaction.response.defer(ephemeral=True)
    await interaction.channel.purge(limit=miktar)
    await interaction.followup.send("🗑️ Temizlendi.", ephemeral=True)

@bot.tree.command(name="destek-panel", description="Destek paneli oluşturur (Yönetici).")
@app_commands.checks.has_permissions(administrator=True)
async def slash_destek_panel(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎫 MC Türkiye - Destek Menüsü", 
        description="Aşağıdaki butonları kullanarak destek ekibimizle iletişime geçebilir ya da aktif kadromuzu görüntüleyebilirsiniz.", 
        color=discord.Color.blurple()
    )
    if BANNER_URL:
        embed.set_image(url=BANNER_URL) # İstek Üzerine: Destek paneline eklenen görsel
        
    await interaction.response.send_message("Panel oluşturuldu.", ephemeral=True)
    await interaction.channel.send(embed=embed, view=DestekPanelView())

@bot.tree.command(name="rol-basvuru", description="Rol başvuru paneli gönderir (Yönetici).")
@app_commands.checks.has_permissions(administrator=True)
async def slash_rol_basvuru(interaction: discord.Interaction):
    embed = discord.Embed(title="Unvan Doğrulama Başvuruları", color=discord.Color.purple())
    await interaction.channel.send(embed=embed, view=RolBasvuruView())

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Bu komutu sadece **Yönetici** kullanabilir!", ephemeral=True)

# =====================================================================
# === OTO GELEN - GİDEN SİSTEMİ (GÖRSEL ENTEGRELİ) ===
# =====================================================================

@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name="genel-sohbet")
    if channel:
        embed = discord.Embed(description=f"{member.mention} aramıza katıldı! Hoş geldin! 🎉", color=discord.Color.green())
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Toplam: {len(member.guild.members)} üye")
        if BANNER_URL: 
            embed.set_image(url=BANNER_URL) # Gelen üye embed altı görseli
        await channel.send(embed=embed)

@bot.event
async def on_member_remove(member):
    channel = discord.utils.get(member.guild.text_channels, name="genel-sohbet")
    if channel:
        embed = discord.Embed(description=f"{member.mention} aramizdan ayrıldı. Görüşmek üzere! 😢", color=discord.Color.red())
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Kalan: {len(member.guild.members)} üye")
        if BANNER_URL: 
            embed.set_image(url=BANNER_URL) # Giden üye embed altı görseli
        await channel.send(embed=embed)

# === DOĞAL DÖNGÜLER VE BAŞLANGIÇ ===
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
