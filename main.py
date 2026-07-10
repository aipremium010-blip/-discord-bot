import discord
from discord.ext import commands, tasks
from discord.ui import View, Button, Select, Modal, TextInput
from discord import app_commands
import os
import asyncio
import time
from datetime import datetime
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

ROL_IDLERI = {
    "Sunucu Sahibi": 1524866585637031962,   # Sunucunuza göre ID'leri güncelleyebilirsiniz
    "Klan Sahibi": 1524866585637031963,
    "Hosting Sahibi": 1524866585637031964,
    "İçerik Üreticisi": 1524866585637031965
}

# === REKLAM FİYATLARI ===
reklam_fiyatlari = {"demir": 100, "altin": 200, "elmas": 300, "netherite": 400}

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
    "demir": {
        "emoji": "🔩",
        "isim": "Demir Paket",
        "fiyat": 100,
        "renk": "#B0B0B0",
        "ozellikler": [
            "Temel reklam hizmetleri",
            "3 günlük kanal size ait",
            "Çekiliş sizden",  # İstek üzerine güncellendi
            "1 everyone hakkı"
        ]
    },
    "altin": {
        "emoji": "🥇",
        "isim": "Altın Paket",
        "fiyat": 200,
        "renk": "#FFD700",
        "ozellikler": [
            "5 günlük reklam paketi",
            "Çekiliş bizden",
            "1 everyone hakkı"
        ]
    },
    "elmas": {
        "emoji": "💎",
        "isim": "Elmas Paket",
        "fiyat": 300,
        "renk": "#00CED1",
        "ozellikler": [
            "7 günlük reklam paketi",
            "Çekiliş bizden",
            "1 everyone + 1 here hakkı"
        ]
    },
    "netherite": {
        "emoji": "⚔️",
        "isim": "Netherite Paket",
        "fiyat": 400,
        "renk": "#4A0080",
        "ozellikler": [
            "14 günlük reklam paketi",
            "Reklam odası",
            "2 everyone + 1 here hakkı",
            "Çekiliş bizden"
        ]
    }
}

# === ONAY/RED ALTYAPISI (BasvuruOnayView) ===
class BasvuruOnayView(View):
    def __init__(self, basvuran_id: int, rol_adi: str):
        super().__init__(timeout=None)
        self.basvuran_id = basvuran_id
        self.rol_adi = rol_adi

    @discord.ui.button(label="Kabul Et", style=discord.ButtonStyle.success, custom_id="basvuru_onay")
    async def kabul_et(self, interaction: discord.Interaction, button: discord.Button):
        guild = interaction.guild
        member = guild.get_member(self.basvuran_id)
        rol_id = ROL_IDLERI.get(self.rol_adi)
        rol = guild.get_role(rol_id) if rol_id else None

        if member and rol:
            await member.add_role(rol)
            embed = interaction.message.embeds[0]
            embed.set_field_at(4, name="Durum", value="✅ Kabul Edildi", inline=False)
            await interaction.message.edit(embed=embed, view=None)
            await interaction.response.send_message(f"{member.mention} kullanıcısına {rol.name} rolü verildi.", ephemeral=True)
            
            try:
                await member.send(f"Tebrikler! **{self.rol_adi}** başvurunuz kabul edildi ve rolünüz tanımlandı.")
            except:
                pass
        else:
            await interaction.response.send_message("Kullanıcı veya rol bulunamadı!", ephemeral=True)

    @discord.ui.button(label="Reddet", style=discord.ButtonStyle.danger, custom_id="basvuru_red")
    async def reddet(self, interaction: discord.Interaction, button: discord.Button):
        member = interaction.guild.get_member(self.basvuran_id)
        embed = interaction.message.embeds[0]
        embed.set_field_at(4, name="Durum", value="❌ Reddedildi", inline=False)
        await interaction.message.edit(embed=embed, view=None)
        await interaction.response.send_message("Başvuru reddedildi.", ephemeral=True)
        
        if member:
            try:
                await member.send(f"Maalesef, **{self.rol_adi}** başvurunuz yetkililer tarafından reddedildi.")
            except:
                pass

# === ROL BAŞVURU MODAL ===
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
            if self.detaylar.value:
                embed.add_field(name="Detaylar", value=self.detaylar.value, inline=False)
            embed.set_footer(text=f"Başvuru Tarihi: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
            
            await basvuru_kanal.send(embed=embed, view=BasvuruOnayView(interaction.user.id, self.rol_adi))

        try:
            dm_embed = discord.Embed(
                title=f"{self.rol_adi} Başvurunuz Alındı",
                description="Başvurunuz incelendikten sonra size dönüş yapılacaktır.",
                color=discord.Color.green()
            )
            await interaction.user.send(embed=dm_embed)
        except:
            pass

# === DESTEK MODAL ===
class DestekModal(Modal, title="Destek Talebi"):
    konu = TextInput(label="Kısaca konunuzdan bahsedin", placeholder="Örn: Reklam almak istiyorum", required=True)

    def __init__(self, kategori_key):
        super().__init__()
        self.kategori_key = kategori_key
        self.emoji, self.kategori_adi = TICKET_KATEGORILERI[kategori_key]

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"**{self.emoji} {self.kategori_adi} Ticketi** açılıyor...",
            ephemeral=True
        )

        support_rol = interaction.guild.get_role(SUPPORT_ROL_ID)
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        if support_rol:
            overwrites[support_rol] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        channel = await interaction.guild.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            overwrites=overwrites
        )

        hesap_acilis = interaction.user.created_at.strftime("%d/%m/%Y")
        ticket_acilis = datetime.now().strftime("%d/%m/%Y %H:%M")

        # İstenen ACILIS SEBEBI kontrolü ve düzeltmesi yapıldı
        embed = discord.Embed(
            title=f"{self.emoji} ACILIS SEBEBI: {self.kategori_adi.upper()}",
            description=f"**Konu:** {self.kategori_adi}\n**Kısaca Konunuz:** {self.konu.value}",
            color=discord.Color.green()
        )
        embed.add_field(name="Oyuncu Adı", value=interaction.user.display_name, inline=True)
        embed.add_field(name="Hesap Açılış Tarihi", value=hesap_acilis, inline=True)
        embed.add_field(name="Ticket Açılış Zamanı", value=ticket_acilis, inline=True)
        embed.add_field(name="Kullanıcı ID", value=interaction.user.id, inline=True)
        embed.add_field(name="Kategori", value=f"{self.emoji} {self.kategori_adi}", inline=True)
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text=f"Ticket ID: {interaction.user.id} | {ticket_acilis}")

        if support_rol:
            await channel.send(f"{support_rol.mention} Yeni destek talebi!", embed=embed)
        else:
            await channel.send(embed=embed)

        await channel.send(view=TicketKapatView())
        await interaction.followup.send(f"Destek talebiniz açıldı: {channel.mention}", ephemeral=True)

# === VIEW'LAR ===

class TicketKapatView(View):
    def __init__(self):
        super().__init__(timeout=None)

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
        self.emoji, self.kategori_adi = TICKET_KATEGORILERI[kategori_key]

    @discord.ui.button(label="Ticket Aç", style=discord.ButtonStyle.success, emoji="🎫")
    async def ticket_ac(self, interaction, button):
        await interaction.response.send_modal(DestekModal(self.kategori_key))

class DestekPanelView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(
        placeholder="Bir kategori seçerek destek talebi açabilirsiniz...",
        options=[
            discord.SelectOption(label="Partnerlik", value="partnerlik", description="Partnerlik başvurusu", emoji="📃"),
            discord.SelectOption(label="Şikayet", value="sikayet", description="Bir şikayet bildirin", emoji="🚨"),
            discord.SelectOption(label="Yetkili Başvurusu", value="yetkili-basvuru", description="Yetkili ekibine katılın", emoji="📙"),
            discord.SelectOption(label="Reklam", value="reklam", description="Reklam başvurusu", emoji="💵"),
            discord.SelectOption(label="Genel", value="genel", description="Genel destek talebi", emoji="📜")
        ]
    )
    async def kategori_sec(self, interaction, select):
        kategori_key = select.values[0]
        emoji, kategori_adi = TICKET_KATEGORILERI[kategori_key]

        embed = discord.Embed(
            title=f"{emoji} {kategori_adi} Desteği",
            description=f"**{kategori_adi}** kategorisinde destek talebi açmak için aşağıdaki butona tıklayın.",
            color=discord.Color.blurple()
        )
        await interaction.response.send_message(embed=embed, view=TicketKonuView(kategori_key), ephemeral=True)

class PaketDetayView(View):
    def __init__(self, paket_key):
        super().__init__(timeout=None)
        self.paket_key = paket_key
        self.detay = PAKET_DETAYLARI[paket_key]

    @discord.ui.button(label="Geri Dön", style=discord.ButtonStyle.secondary, emoji="◀️")
    async def geri_don(self, interaction, button):
        await interaction.response.edit_message(embed=self.paketler_embed(), view=PaketlerView())

    def paketler_embed(self):
        embed = discord.Embed(
            title="MC Türkiye Topluluk Sunucusu - Reklam Hizmetleri",
            description="Detaylı bilgi almak için lütfen <#1524866586693865492> kanalını inceleyiniz.\nAşağıdaki menüden paket seçerek de özellik detaylarına bakabilirsiniz.",
            color=discord.Color.gold()
        )
        return embed

class PaketlerView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(
        placeholder="Bir paket seçiniz...",
        options=[
            discord.SelectOption(label="Demir Paket - 100TL", value="demir", description="3 günlük kanal + çekiliş + 1 everyone"),
            discord.SelectOption(label="Altın Paket - 200TL", value="altin", description="5 günlük + çekiliş bizden + 1 everyone"),
            discord.SelectOption(label="Elmas Paket - 300TL", value="elmas", description="7 günlük + çekiliş bizden + everyone+here"),
            discord.SelectOption(label="Netherite Paket - 400TL", value="netherite", description="14 günlük + oda + 2 everyone + here")
        ]
    )
    async def paket_sec(self, interaction, select):
        paket_key = select.values[0]
        detay = PAKET_DETAYLARI[paket_key]

        embed = discord.Embed(
            title=f"{detay['emoji']} {detay['isim']}",
            description=f"**Fiyat:** {detay['fiyat']}TL",
            color=discord.Color(int(detay['renk'].replace('#', ''), 16))
        )

        ozellikler_text = "\n".join([f"- {oz}" for oz in detay['ozellikler']])
        embed.add_field(name="Özellikler", value=ozellikler_text, inline=False)
        embed.set_footer(text="Satın almak için yetkililere ulaşın.")

        await interaction.response.edit_message(embed=embed, view=PaketDetayView(paket_key))

class RolBasvuruView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Sunucu Sahibi", style=discord.ButtonStyle.primary, emoji="👑")
    async def sunucu_sahibi(self, interaction, button):
        await interaction.response.send_modal(RolBasvuruModal("Sunucu Sahibi"))

    @discord.ui.button(label="Klan Sahibi", style=discord.ButtonStyle.primary, emoji="⚔️")
    async def klan_sahibi(self, interaction, button):
        await interaction.response.send_modal(RolBasvuruModal("Klan Sahibi"))

    @discord.ui.button(label="Hosting Sahibi", style=discord.ButtonStyle.primary, emoji="🖥️")
    async def hosting_sahibi(self, interaction, button):
        await interaction.response.send_modal(RolBasvuruModal("Hosting Sahibi"))

    @discord.ui.button(label="İçerik Üreticisi", style=discord.ButtonStyle.primary, emoji="🎬")
    async def icerik_ureticisi(self, interaction, button):
        await interaction.response.send_modal(RolBasvuruModal("İçerik Üreticisi"))

# === SLASH KOMUTLARI ===

@bot.tree.command(name="selam", description="Selam verir")
async def slash_selam(interaction):
    await interaction.response.send_message(f"Selam {interaction.user.mention}!")

@bot.tree.command(name="ping", description="Bot gecikmesini gösterir")
async def slash_ping(interaction):
    await interaction.response.send_message(f"Pong! Gecikme: {round(bot.latency * 1000)}ms")

@bot.tree.command(name="paketler", description="Reklam paketlerini gösterir")
async def slash_paketler(interaction):
    embed = discord.Embed(
        title="MC Türkiye Topluluk Sunucusu - Reklam Hizmetleri",
        description="Detaylı bilgi almak için lütfen <#1524866586693865492> kanalını inceleyiniz.\nAşağıdaki menüden paket seçerek de özellik detaylarına bakabilirsiniz.",
        color=discord.Color.gold()
    )
    await interaction.response.send_message(embed=embed, view=PaketlerView())

@bot.tree.command(name="yardim", description="Tüm komutları gösterir")
async def slash_yardim(interaction):
    await interaction.response.send_message("""**Komutlar:**
`/selam` - Selam verir
`/ping` - Bot gecikmesini gösterir
`/yardim` - Bu mesajı gösterir
`/paketler` - Reklam paketlerini gösterir
`/ilan-ver` - Pazar alanında ilan oluşturur
`/destek` - Destek talebi oluşturur
`/lock` - Kanalı kilitler
`/unlock` - Kanal kilidini açar
`/sil` - Mesaj siler

**Yönetici Komutları:**
`/mesaj` - Embed mesaj gönderir
`/rol-basvuru` - Rol başvuru paneli
`/destek-panel` - Destek paneli
`/reklam-fiyat-ayarla` - Reklam fiyatlarını ayarlar""")

@bot.tree.command(name="ilan-ver", description="Pazar alanında ilan oluşturur")
@app_commands.describe(urun="Ürün adı", fiyat="Ürün fiyatı", aciklama="Ürün açıklaması")
async def slash_ilan_ver(interaction, urun: str, fiyat: str, aciklama: str):
    pazar_channel = interaction.guild.get_channel(PAZAR_KANAL_ID)
    if not pazar_channel:
        await interaction.response.send_message("Pazar alanı kanalı bulunamadı!", ephemeral=True)
        return
    embed = discord.Embed(title="Yeni İlan", color=discord.Color.orange())
    embed.add_field(name="İlan Sahibi", value=interaction.user.mention, inline=False)
    embed.add_field(name="Ürün", value=urun, inline=True)
    embed.add_field(name="Fiyat", value=fiyat, inline=True)
    embed.add_field(name="Açıklama", value=aciklama, inline=False)
    embed.set_footer(text=f"İlan Tarihi: {datetime.now().strftime('%d/%m/%Y')}")

    msg = await pazar_channel.send(embed=embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")

    await interaction.response.send_message("İlanınız pazar alanına gönderildi!", ephemeral=True)

@bot.tree.command(name="destek", description="Destek talebi oluşturur")
async def slash_destek(interaction):
    await interaction.response.send_message("Destek talebi oluşturmak için `/destek-panel` komutunu kullanın.", ephemeral=True)

@bot.tree.command(name="lock", description="Kanalı kilitler (Yetkili)")
@app_commands.checks.has_permissions(manage_channels=True)
async def slash_lock(interaction, kanal: discord.TextChannel = None):
    channel = kanal or interaction.channel
    await channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message(f"{channel.mention} kilitlendi!", ephemeral=True)

@slash_lock.error
async def slash_lock_error(interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("Yetkiniz yok!", ephemeral=True)

@bot.tree.command(name="unlock", description="Kanal kilidini açar (Yetkili)")
@app_commands.checks.has_permissions(manage_channels=True)
async def slash_unlock(interaction, kanal: discord.TextChannel = None):
    channel = kanal or interaction.channel
    await channel.set_permissions(interaction.guild.default_role, send_messages=True)
    await interaction.response.send_message(f"{channel.mention} açıldı!", ephemeral=True)

@slash_unlock.error
async def slash_unlock_error(interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("Yetkiniz yok!", ephemeral=True)

@bot.tree.command(name="sil", description="Belirtilen sayıda mesaj siler (Yetkili)")
@app_commands.checks.has_permissions(manage_messages=True)
@app_commands.describe(miktar="Silinecek mesaj sayısı (1-100)")
async def slash_sil(interaction, miktar: int):
    if miktar < 1 or miktar > 100:
        await interaction.response.send_message("1-100 arası girin!", ephemeral=True)
        return
    await interaction.channel.purge(limit=miktar)
    await interaction.response.send_message(f"{miktar} mesaj silindi!", ephemeral=True)

@slash_sil.error
async def slash_sil_error(interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("Yetkiniz yok!", ephemeral=True)

@bot.tree.command(name="reklam-fiyat-ayarla", description="Reklam paket fiyatlarını ayarlar (Yetkili)")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(paket="Paket adı (demir, altin, elmas, netherite)", fiyat="Yeni fiyat")
async def slash_reklam_fiyat_ayarla(interaction, paket: str, fiyat: int):
    paket = paket.lower()
    if paket not in reklam_fiyatlari:
        await interaction.response.send_message("Geçersiz paket!", ephemeral=True)
        return
    reklam_fiyatlari[paket] = fiyat
    PAKET_DETAYLARI[paket]["fiyat"] = fiyat
    await interaction.response.send_message(f"{paket.capitalize()} Paket fiyatı {fiyat}TL olarak güncellendi!", ephemeral=True)

@slash_reklam_fiyat_ayarla.error
async def slash_reklam_fiyat_ayarla_error(interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("Yetkiniz yok!", ephemeral=True)

@bot.tree.command(name="mesaj", description="Belirtilen kanala embed mesaj gönderir (Yetkili)")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(kanal="Mesajın gönderileceği kanal", mesaj="Gönderilecek mesaj", baslik="Mesaj başlığı", renk="Embed rengi (kirmizi, yesil, mavi, sari, mor)")
async def slash_mesaj(interaction, kanal: discord.TextChannel, mesaj: str, baslik: str = None, renk: str = "mavi"):
    renkler = {"kirmizi": discord.Color.red(), "yesil": discord.Color.green(), "mavi": discord.Color.blue(), "sari": discord.Color.gold(), "mor": discord.Color.purple()}
    embed = discord.Embed(description=mesaj, color=renkler.get(renk.lower(), discord.Color.blue()))
    if baslik:
        embed.title = baslik
    embed.set_footer(text=f"Gönderen: {interaction.user.display_name}")
    embed.timestamp = discord.utils.utcnow()
    await kanal.send(embed=embed)
    await interaction.response.send_message(f"Mesaj {kanal.mention} kanalına gönderildi!", ephemeral=True)

@slash_mesaj.error
async def slash_mesaj_error(interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("Yetkiniz yok!", ephemeral=True)

@bot.tree.command(name="rol-basvuru", description="Rol başvuru paneli oluşturur (Yetkili)")
@app_commands.checks.has_permissions(administrator=True)
async def slash_rol_basvuru(interaction):
    embed = discord.Embed(
        title="Unvan Doğrulama Başvuruları",
        description="Sunucu sahibi, klan lideri, hosting firması veya içerik üreticisi unvanlarına sahipseniz rollerinizi teslim almak için aşağıdaki butona tıklayın.",
        color=discord.Color.purple()
    )
    await interaction.response.send_message(embed=embed, view=RolBasvuruView())

@bot.tree.command(name="destek-panel", description="Destek paneli oluşturur (Yetkili)")
@app_commands.checks.has_permissions(administrator=True)
async def slash_destek_panel(interaction):
    embed = discord.Embed(
        title="Destek Menüsü",
        description="Aşağıdaki menüden destek talebi açabilirsiniz.\n\n• Yetkilileri meşgul etmek yasaktır.\n• Destek taleplerinizi kategorilere göre açın.\n• Uygun kanal seçildikten sonra destek ekibi bilgilendirilecektir.",
        color=discord.Color.blurple()
    )
    await interaction.response.send_message(embed=embed, view=DestekPanelView())

# === KEEP ALIVE ===
@tasks.loop(seconds=30)
async def keep_alive():
    try:
        req = urllib.request.Request("http://localhost:8080/ping", method="GET")
        with urllib.request.urlopen(req, timeout=5) as response:
            pass
    except Exception as e:
        print(f"Keep-alive ping hatası: {e}")

# === HOŞ GELDİN MESAJLARI ===
@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name="genel-sohbet")
    if channel:
        embed = discord.Embed(
            description=f"{member.mention} aramıza katıldı! Hoş geldin!",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Toplam: {len(member.guild.members)} üye")
        await channel.send(embed=embed)

@bot.event
async def on_member_remove(member):
    channel = discord.utils.get(member.guild.text_channels, name="genel-sohbet")
    if channel:
        embed = discord.Embed(
            description=f"{member.mention} aramizdan ayrıldı. Görüşmek üzere!",
            color=discord.Color.red()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Kalan: {len(member.guild.members)} üye")
        await channel.send(embed=embed)

@bot.event
async def on_message(message):
    if message.channel.id == PAZAR_KANAL_ID and message.author != bot.user:
        if message.embeds:
            await message.add_reaction("✅")
            await message.add_reaction("❌")
    await bot.process_commands(message)

# === BAĞLANTI KORUMA ===
@bot.event
async def on_disconnect():
    print(f"Bağlantı kesildi! {datetime.now().strftime('%H:%M:%S')}")

@bot.event
async def on_resumed():
    print(f"Bağlantı yenilendi! {datetime.now().strftime('%H:%M:%S')}")

# === ON_READY ===
_synced = False

@bot.event
async def on_ready():
    global _synced
    print(f"Bot aktif: {bot.user}")

    if not _synced:
        try:
            for guild in bot.guilds:
                try:
                    synced = await bot.tree.sync(guild=guild)
                    print(f"{guild.name}: {len(synced)} komut senkronize edildi")
                except Exception as e:
                    print(f"{guild.name} hata: {e}")
            _synced = True
            print("Tüm komutlar senkronize edildi!")
        except Exception as e:
            print(f"Senkronizasyon hatası: {e}")

    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.watching, name="/yardim"),
        status=discord.Status.online
    )

    if not keep_alive.is_running():
        keep_alive.start()
        print("Keep-alive başlatıldı!")

# === BAŞLAT ===
print("Bot başlatılıyor...")

TOKEN = os.environ.get('DISCORD_TOKEN', '')
if not TOKEN:
    print("HATA: DISCORD_TOKEN bulunamadı!")
    print("Lütfen Environment Variables'dan DISCORD_TOKEN'ı ayarlayın.")
    exit(1)

bot.run(TOKEN, reconnect=True)
