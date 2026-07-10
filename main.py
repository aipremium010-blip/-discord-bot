import discord
from discord.ext import commands
from discord.ui import View, Button, Select
from discord import app_commands
import os
import asyncio
from datetime import datetime
from flask import Flask
from threading import Thread

# === WEB SERVER (Render icin keep-alive) ===
app = Flask('')

@app.route('/')
def home():
    return "Bot aktif! 🚀"

def run_web():
    app.run(host='0.0.0.0', port=8080)

Thread(target=run_web, daemon=True).start()

# === BOT AYARLARI ===
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)

# === KANAL/ROL ID'LERI ===
BASVURU_KANAL_ID = 1524879141793435689
PAZAR_KANAL_ID = 1524866586912227330
SUPPORT_ROL_ID = 1524866585637031961

# === REKLAM FIYATLARI ===
reklam_fiyatlari = {"demir": 50, "altin": 100, "elmas": 200, "netherite": 500}

# === TICKET KATEGORILERI ===
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
        "fiyat": 50,
        "renk": "#B0B0B0",
        "ozellikler": [
            "Temel reklam hizmetleri",
            "1 hafta sureli reklam",
            "Standart konumlandirma",
            "Gunluk 1 paylasim"
        ]
    },
    "altin": {
        "emoji": "🥇",
        "isim": "Altin Paket",
        "fiyat": 100,
        "renk": "#FFD700",
        "ozellikler": [
            "Gelismis reklam hizmetleri",
            "2 hafta sureli reklam",
            "On plana cikan konumlandirma",
            "Gunluk 2 paylasim",
            "@here etiketi (haftada 1)"
        ]
    },
    "elmas": {
        "emoji": "💎",
        "isim": "Elmas Paket",
        "fiyat": 200,
        "renk": "#00CED1",
        "ozellikler": [
            "Premium reklam hizmetleri",
            "1 ay sureli reklam",
            "En ust konumlandirma",
            "Gunluk 3 paylasim",
            "@here etiketi (haftada 2)",
            "Ozel banner tasarimi"
        ]
    },
    "netherite": {
        "emoji": "⚔️",
        "isim": "Netherite Paket",
        "fiyat": 500,
        "renk": "#4A0080",
        "ozellikler": [
            "VIP reklam hizmetleri",
            "3 ay sureli reklam",
            "En ust konumlandirma + sabit",
            "Sinirsiz paylasim",
            "@here + @everyone etiketi",
            "Ozel banner + video tasarimi",
            "7/24 destek hatti",
            "Partnerlik hakki"
        ]
    }
}

# === VIEW'LAR ===

class TicketKapatView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Talebi Kapat", style=discord.ButtonStyle.danger)
    async def kapat(self, interaction, button):
        support_rol = interaction.guild.get_role(SUPPORT_ROL_ID)
        if interaction.user.guild_permissions.administrator or (support_rol and support_rol in interaction.user.roles):
            await interaction.response.send_message("🔒 Ticket 5 saniye sonra kapatilacak...")
            await asyncio.sleep(5)
            await interaction.channel.delete()
        else:
            await interaction.response.send_message("❌ Bu islem icin yetkiniz yok!", ephemeral=True)

class TicketKonuView(View):
    def __init__(self, kategori_key):
        super().__init__(timeout=None)
        self.kategori_key = kategori_key
        self.emoji, self.kategori_adi = TICKET_KATEGORILERI[kategori_key]

    @discord.ui.button(label="Ticket Ac", style=discord.ButtonStyle.success)
    async def ticket_ac(self, interaction, button):
        await interaction.response.send_message(
            f"**{self.emoji} {self.kategori_adi} Ticketi**\n\n"
            f"Lutfen asagidaki bilgileri **bu kanala** yazin:\n\n"
            f"1. **Kisaca Konunuz Nedir?**\n"
            f"2. **Oyuncu Adiniz:**\n"
            f"3. **Detayli Aciklama:**\n\n"
            f"Yetkili ekibi en kisa surede size donus yapacaktir.",
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

        embed = discord.Embed(
            title=f"{self.emoji} ACIKIS SEBEBI: {self.kategori_adi.upper()}",
            description=f"**Konu:** {self.kategori_adi}\n**Kisaca Konunuz:** (Kullanici aciklamasi bekleniyor)",
            color=discord.Color.green()
        )
        embed.add_field(name="👤 Oyuncu Adi", value=interaction.user.display_name, inline=True)
        embed.add_field(name="📅 Hesap Acilis Tarihi", value=hesap_acilis, inline=True)
        embed.add_field(name="🕐 Ticket Acilis Zamani", value=ticket_acilis, inline=True)
        embed.add_field(name="🆔 Kullanici ID", value=interaction.user.id, inline=True)
        embed.add_field(name="📋 Kategori", value=f"{self.emoji} {self.kategori_adi}", inline=True)
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text=f"Ticket ID: {interaction.user.id} | {ticket_acilis}")

        if support_rol:
            await channel.send(f"{support_rol.mention} Yeni destek talebi!", embed=embed)
        else:
            await channel.send(embed=embed)

        await channel.send(view=TicketKapatView())
        await interaction.followup.send(f"✅ Destek talebiniz acildi: {channel.mention}", ephemeral=True)

class DestekPanelView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(
        placeholder="Bir kategori secerek destek talebi acabilirsiniz...",
        options=[
            discord.SelectOption(label="📃 Partnerlik", value="partnerlik", description="Partnerlik basvurusu"),
            discord.SelectOption(label="🚨 Sikayet", value="sikayet", description="Bir sikayet bildirin"),
            discord.SelectOption(label="📙 Yetkili Basvurusu", value="yetkili-basvuru", description="Yetkili ekibine katilin"),
            discord.SelectOption(label="💵 Reklam", value="reklam", description="Reklam basvurusu"),
            discord.SelectOption(label="📜 Genel", value="genel", description="Genel destek talebi")
        ]
    )
    async def kategori_sec(self, interaction, select):
        kategori_key = select.values[0]
        emoji, kategori_adi = TICKET_KATEGORILERI[kategori_key]

        embed = discord.Embed(
            title=f"{emoji} {kategori_adi} Destegi",
            description=f"**{kategori_adi}** kategorisinde destek talebi acmak icin asagidaki butona tiklayin.",
            color=discord.Color.blurple()
        )
        await interaction.response.send_message(embed=embed, view=TicketKonuView(kategori_key), ephemeral=True)

class PaketDetayView(View):
    def __init__(self, paket_key):
        super().__init__(timeout=None)
        self.paket_key = paket_key
        self.detay = PAKET_DETAYLARI[paket_key]

    @discord.ui.button(label="Geri Don", style=discord.ButtonStyle.secondary)
    async def geri_don(self, interaction, button):
        await interaction.response.edit_message(embed=self.paketler_embed(), view=PaketlerView())

    def paketler_embed(self):
        embed = discord.Embed(
            title="💎 Reklam Paketleri",
            description="Asagidaki paketlerden birini secerek detaylari goruntuleyebilirsiniz.",
            color=discord.Color.gold()
        )
        for key, detay in PAKET_DETAYLARI.items():
            embed.add_field(
                name=f"{detay['emoji']} {detay['isim']}",
                value=f"Fiyat: {detay['fiyat']}TL",
                inline=False
            )
        return embed

class PaketlerView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(
        placeholder="Bir paket seciniz...",
        options=[
            discord.SelectOption(label="🔩 Demir Paket", value="demir", description="Temel ozellikler - 50TL"),
            discord.SelectOption(label="🥇 Altin Paket", value="altin", description="Gelismis ozellikler - 100TL"),
            discord.SelectOption(label="💎 Elmas Paket", value="elmas", description="Premium ozellikler - 200TL"),
            discord.SelectOption(label="⚔️ Netherite Paket", value="netherite", description="VIP ozellikler - 500TL")
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

        ozellikler_text = "\n".join([f"✅ {oz}" for oz in detay['ozellikler']])
        embed.add_field(name="📋 Ozellikler", value=ozellikler_text, inline=False)
        embed.set_footer(text="Satin almak icin yetkililere ulasin.")

        await interaction.response.edit_message(embed=embed, view=PaketDetayView(paket_key))

class RolBasvuruView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="👑 Sunucu Sahibi", style=discord.ButtonStyle.primary)
    async def sunucu_sahibi(self, interaction, button):
        await self.basvuru_yap(interaction, "Sunucu Sahibi")

    @discord.ui.button(label="⚔️ Klan Sahibi", style=discord.ButtonStyle.primary)
    async def klan_sahibi(self, interaction, button):
        await self.basvuru_yap(interaction, "Klan Sahibi")

    @discord.ui.button(label="🎥 Yayinci", style=discord.ButtonStyle.primary)
    async def yayinci(self, interaction, button):
        await self.basvuru_yap(interaction, "Yayinci")

    @discord.ui.button(label="🖥️ Hosting Sahibi", style=discord.ButtonStyle.primary)
    async def hosting_sahibi(self, interaction, button):
        await self.basvuru_yap(interaction, "Hosting Sahibi")

    @discord.ui.button(label="📝 Icerik Ureticisi", style=discord.ButtonStyle.primary)
    async def icerik_ureticisi(self, interaction, button):
        await self.basvuru_yap(interaction, "Icerik Ureticisi")

    async def basvuru_yap(self, interaction, rol_adi):
        await interaction.response.send_message(
            f"**{rol_adi} Basvuru Formu**\n\n"
            f"Basvurunuzu tamamlamak icin lutfen su bilgileri **bu kanala** yazin:\n"
            f"1. **Projenizin/Sunucunuzun Adi:**\n"
            f"2. **Kanti/Discord/Web Linki:**\n"
            f"3. **Eklemek Istediginiz Detaylar:**\n\n"
            f"Basvurunuz incelendikten sonra size donus yapilacaktir.",
            ephemeral=True
        )

        basvuru_kanal = interaction.guild.get_channel(BASVURU_KANAL_ID)
        if basvuru_kanal:
            embed = discord.Embed(title=f"📝 {rol_adi} Basvurusu", color=discord.Color.gold())
            embed.add_field(name="Basvuran", value=interaction.user.mention, inline=False)
            embed.add_field(name="Rol", value=rol_adi, inline=False)
            embed.add_field(name="Durum", value="⏳ Beklemede", inline=False)
            embed.set_footer(text=f"Basvuru Tarihi: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
            await basvuru_kanal.send(embed=embed)

        try:
            dm_embed = discord.Embed(
                title=f"📝 {rol_adi} Basvurunuz Alindi",
                description="Basvurunuz incelendikten sonra size donus yapilacaktir.",
                color=discord.Color.green()
            )
            await interaction.user.send(embed=dm_embed)
        except:
            pass

# === SLASH KOMUTLARI ===

@bot.tree.command(name="selam", description="Selam verir")
async def slash_selam(interaction):
    await interaction.response.send_message(f"Selam {interaction.user.mention}! 👋")

@bot.tree.command(name="ping", description="Bot gecikmesini gosterir")
async def slash_ping(interaction):
    await interaction.response.send_message(f"Pong! 🏓 Gecikme: {round(bot.latency * 1000)}ms")

@bot.tree.command(name="paketler", description="Reklam paketlerini gosterir")
async def slash_paketler(interaction):
    embed = discord.Embed(
        title="💎 Reklam Paketleri",
        description="Asagidaki paketlerden birini secerek detaylari goruntuleyebilirsiniz.",
        color=discord.Color.gold()
    )
    for key, detay in PAKET_DETAYLARI.items():
        embed.add_field(
            name=f"{detay['emoji']} {detay['isim']}",
            value=f"Fiyat: {detay['fiyat']}TL",
            inline=False
        )
    await interaction.response.send_message(embed=embed, view=PaketlerView())

@bot.tree.command(name="yardim", description="Tum komutlari gosterir")
async def slash_yardim(interaction):
    await interaction.response.send_message("""**📋 Komutlar:**
`/selam` - Selam verir
`/ping` - Bot gecikmesini gosterir
`/yardim` - Bu mesaji gosterir
`/paketler` - Reklam paketlerini gosterir
`/ilan-ver` - Pazar alaninda ilan olusturur
`/destek` - Destek talebi olusturur
`/lock` - Kanali kilitler
`/unlock` - Kanal kilidini acar
`/sil` - Mesaj siler

**👑 Yonetici Komutlari:**
`/mesaj` - Embed mesaj gonderir
`/rol-basvuru` - Rol basvuru paneli
`/destek-panel` - Destek paneli
`/reklam-fiyat-ayarla` - Reklam fiyatlarini ayarlar""")

@bot.tree.command(name="ilan-ver", description="Pazar alaninda ilan olusturur")
@app_commands.describe(urun="Urun adi", fiyat="Urun fiyati", aciklama="Urun aciklamasi")
async def slash_ilan_ver(interaction, urun: str, fiyat: str, aciklama: str):
    pazar_channel = interaction.guild.get_channel(PAZAR_KANAL_ID)
    if not pazar_channel:
        await interaction.response.send_message("❌ Pazar alani kanali bulunamadi!", ephemeral=True)
        return
    embed = discord.Embed(title="🛒 Yeni Ilan", color=discord.Color.orange())
    embed.add_field(name="Ilan Sahibi", value=interaction.user.mention, inline=False)
    embed.add_field(name="Urun", value=urun, inline=True)
    embed.add_field(name="Fiyat", value=fiyat, inline=True)
    embed.add_field(name="Aciklama", value=aciklama, inline=False)
    embed.set_footer(text=f"Ilan Tarihi: {datetime.now().strftime('%d/%m/%Y')}")

    msg = await pazar_channel.send(embed=embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")

    await interaction.response.send_message("✅ Ilaniniz pazar alanina gonderildi!", ephemeral=True)

@bot.tree.command(name="destek", description="Destek talebi olusturur")
async def slash_destek(interaction):
    await interaction.response.send_message("Destek talebi olusturmak icin `/destek-panel` komutunu kullanin.", ephemeral=True)

@bot.tree.command(name="lock", description="Kanali kilitler (Yetkili)")
@app_commands.checks.has_permissions(manage_channels=True)
async def slash_lock(interaction, kanal: discord.TextChannel = None):
    channel = kanal or interaction.channel
    await channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message(f"🔒 {channel.mention} kilitlendi!", ephemeral=True)

@slash_lock.error
async def slash_lock_error(interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Yetkiniz yok!", ephemeral=True)

@bot.tree.command(name="unlock", description="Kanal kilidini acar (Yetkili)")
@app_commands.checks.has_permissions(manage_channels=True)
async def slash_unlock(interaction, kanal: discord.TextChannel = None):
    channel = kanal or interaction.channel
    await channel.set_permissions(interaction.guild.default_role, send_messages=True)
    await interaction.response.send_message(f"🔓 {channel.mention} acildi!", ephemeral=True)

@slash_unlock.error
async def slash_unlock_error(interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Yetkiniz yok!", ephemeral=True)

@bot.tree.command(name="sil", description="Belirtilen sayida mesaj siler (Yetkili)")
@app_commands.checks.has_permissions(manage_messages=True)
@app_commands.describe(miktar="Silinecek mesaj sayisi (1-100)")
async def slash_sil(interaction, miktar: int):
    if miktar < 1 or miktar > 100:
        await interaction.response.send_message("❌ 1-100 arasi girin!", ephemeral=True)
        return
    await interaction.channel.purge(limit=miktar)
    await interaction.response.send_message(f"🗑️ {miktar} mesaj silindi!", ephemeral=True)

@slash_sil.error
async def slash_sil_error(interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Yetkiniz yok!", ephemeral=True)

@bot.tree.command(name="reklam-fiyat-ayarla", description="Reklam paket fiyatlarini ayarlar (Yetkili)")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(paket="Paket adi (demir, altin, elmas, netherite)", fiyat="Yeni fiyat")
async def slash_reklam_fiyat_ayarla(interaction, paket: str, fiyat: int):
    paket = paket.lower()
    if paket not in reklam_fiyatlari:
        await interaction.response.send_message("❌ Gecersiz paket!", ephemeral=True)
        return
    reklam_fiyatlari[paket] = fiyat
    PAKET_DETAYLARI[paket]["fiyat"] = fiyat
    await interaction.response.send_message(f"✅ {paket.capitalize()} Paket fiyati {fiyat}TL olarak guncellendi!", ephemeral=True)

@slash_reklam_fiyat_ayarla.error
async def slash_reklam_fiyat_ayarla_error(interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Yetkiniz yok!", ephemeral=True)

@bot.tree.command(name="mesaj", description="Belirtilen kanala embed mesaj gonderir (Yetkili)")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(kanal="Mesajin gonderilecegi kanal", mesaj="Gonderilecek mesaj", baslik="Mesaj basligi", renk="Embed rengi (kirmizi, yesil, mavi, sari, mor)")
async def slash_mesaj(interaction, kanal: discord.TextChannel, mesaj: str, baslik: str = None, renk: str = "mavi"):
    renkler = {"kirmizi": discord.Color.red(), "yesil": discord.Color.green(), "mavi": discord.Color.blue(), "sari": discord.Color.gold(), "mor": discord.Color.purple()}
    embed = discord.Embed(description=mesaj, color=renkler.get(renk.lower(), discord.Color.blue()))
    if baslik:
        embed.title = baslik
    embed.set_footer(text=f"Gonderen: {interaction.user.display_name}")
    embed.timestamp = discord.utils.utcnow()
    await kanal.send(embed=embed)
    await interaction.response.send_message(f"✅ Mesaj {kanal.mention} kanalina gonderildi!", ephemeral=True)

@slash_mesaj.error
async def slash_mesaj_error(interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Yetkiniz yok!", ephemeral=True)

@bot.tree.command(name="rol-basvuru", description="Rol basvuru paneli olusturur (Yetkili)")
@app_commands.checks.has_permissions(administrator=True)
async def slash_rol_basvuru(interaction):
    embed = discord.Embed(
        title="👑 Unvan Dogrulama Basvurulari",
        description="Sunucu sahibi, klan lideri, yayinci, hosting firmasi veya icerik ureticisi unvanlarina sahipseniz rollerinizi teslim almak icin asagidaki butona tiklayin.",
        color=discord.Color.purple()
    )
    await interaction.response.send_message(embed=embed, view=RolBasvuruView())

@bot.tree.command(name="destek-panel", description="Destek paneli olusturur (Yetkili)")
@app_commands.checks.has_permissions(administrator=True)
async def slash_destek_panel(interaction):
    embed = discord.Embed(
        title="🔔 Destek Menusu",
        description="Asagidaki menuden destek talebi acabilirsiniz.\n\n• Yetkilileri mesgul etmek yasaktir.\n• Destek taleplerinizi kategorilere gore acin.\n• Uygun kanal secildikten sonra destek ekibi bilgilendirilecektir.",
        color=discord.Color.blurple()
    )
    await interaction.response.send_message(embed=embed, view=DestekPanelView())

# === EVENT'LER ===

@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name="genel-sohbet")
    if channel:
        embed = discord.Embed(
            title="🎉 Hos Geldin!",
            description=f"{member.mention} aramiza katildi! Hos geldin!",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="👤 Uye", value=member.display_name, inline=True)
        embed.add_field(name="📅 Hesap Tarihi", value=member.created_at.strftime("%d/%m/%Y"), inline=True)
        embed.add_field(name="👥 Toplam Uye", value=len(member.guild.members), inline=True)
        embed.set_footer(text=f"Katilma Zamani: {datetime.now().strftime('%H:%M')}")
        await channel.send(embed=embed)

@bot.event
async def on_member_remove(member):
    channel = discord.utils.get(member.guild.text_channels, name="genel-sohbet")
    if channel:
        embed = discord.Embed(
            title="👋 Gule Gule!",
            description=f"{member.mention} aramizdan ayrildi. Gorusmek uzere!",
            color=discord.Color.red()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="👤 Uye", value=member.display_name, inline=True)
        embed.add_field(name="📅 Sunucuda Kaldigi Sure", value="N/A", inline=True)
        embed.add_field(name="👥 Kalan Uye", value=len(member.guild.members), inline=True)
        embed.set_footer(text=f"Ayrilma Zamani: {datetime.now().strftime('%H:%M')}")
        await channel.send(embed=embed)

@bot.event
async def on_message(message):
    if message.channel.id == PAZAR_KANAL_ID and message.author != bot.user:
        if message.embeds:
            await message.add_reaction("✅")
            await message.add_reaction("❌")
    await bot.process_commands(message)

@bot.event
async def on_ready():
    print(f"✅ {bot.user} aktif!")
    try:
        synced = await bot.tree.sync()
        print(f"🔄 {len(synced)} slash komutu senkronize edildi!")
    except Exception as e:
        print(f"❌ Hata: {e}")

# === BASLAT ===
print("Bot baslatiliyor...")
bot.run(os.environ['DISCORD_TOKEN'])
