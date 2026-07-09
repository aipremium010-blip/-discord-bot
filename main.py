import discord
from discord.ext import commands
from discord.ui import View, Button, Select
from discord import app_commands
import os
import asyncio
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

reklam_fiyatlari = {"demir": 50, "altin": 100, "elmas": 200, "netherite": 500}

# === TICKET ===
class TicketKapatView(View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="Talebi Kapat", style=discord.ButtonStyle.danger)
    async def kapat(self, interaction, button):
        support_rol = interaction.guild.get_role(SUPPORT_ROL_ID)
        if interaction.user.guild_permissions.administrator or (support_rol and support_rol in interaction.user.roles):
            await interaction.response.send_message("Ticket kapatılıyor...")
            await asyncio.sleep(5)
            await interaction.channel.delete()
        else:
            await interaction.response.send_message("Yetkiniz yok!", ephemeral=True)

class TicketOlusturView(View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.select(
        placeholder="Destek konusu seçin...",
        options=[
            discord.SelectOption(label="Partnerlik", value="partnerlik"),
            discord.SelectOption(label="Sikayet", value="sikayet"),
            discord.SelectOption(label="Yetkili Basvuru", value="yetkili-basvuru"),
            discord.SelectOption(label="Reklam", value="reklam"),
            discord.SelectOption(label="Genel", value="genel")
        ]
    )
    async def kategori_sec(self, interaction, select):
        kategori = select.values[0]
        support_rol = interaction.guild.get_role(SUPPORT_ROL_ID)
        
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        if support_rol:
            overwrites[support_rol] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        
        channel = await interaction.guild.create_text_channel(name=f"ticket-{interaction.user.name}", overwrites=overwrites)
        
        embed = discord.Embed(title=f"Destek Talebi: {kategori}", color=discord.Color.green())
        embed.add_field(name="Kategori", value=kategori, inline=True)
        embed.add_field(name="Kullanici", value=interaction.user.mention, inline=True)
        
        if support_rol:
            await channel.send(f"{support_rol.mention} Yeni destek talebi!", embed=embed)
        else:
            await channel.send(embed=embed)
        
        await channel.send(view=TicketKapatView())
        await interaction.response.send_message(f"Destek talebiniz acildi: {channel.mention}", ephemeral=True)

# === ROL BASVURU ===
class RolBasvuruView(View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="Sunucu Sahibi", style=discord.ButtonStyle.primary)
    async def sunucu_sahibi(self, interaction, button):
        await self.basvuru_yap(interaction, "Sunucu Sahibi")
    
    @discord.ui.button(label="Klan Sahibi", style=discord.ButtonStyle.primary)
    async def klan_sahibi(self, interaction, button):
        await self.basvuru_yap(interaction, "Klan Sahibi")
    
    @discord.ui.button(label="Yayinci", style=discord.ButtonStyle.primary)
    async def yayinci(self, interaction, button):
        await self.basvuru_yap(interaction, "Yayinci")
    
    @discord.ui.button(label="Hosting Sahibi", style=discord.ButtonStyle.primary)
    async def hosting_sahibi(self, interaction, button):
        await self.basvuru_yap(interaction, "Hosting Sahibi")
    
    @discord.ui.button(label="Icerik Ureticisi", style=discord.ButtonStyle.primary)
    async def icerik_ureticisi(self, interaction, button):
        await self.basvuru_yap(interaction, "Icerik Ureticisi")
    
    async def basvuru_yap(self, interaction, rol_adi):
        await interaction.response.send_message(f"{rol_adi} basvurunuz alindi! Yetkili ekibine bildirildi.", ephemeral=True)
        
        basvuru_kanal = interaction.guild.get_channel(BASVURU_KANAL_ID)
        if basvuru_kanal:
            embed = discord.Embed(title=f"{rol_adi} Basvurusu", color=discord.Color.gold())
            embed.add_field(name="Basvuran", value=interaction.user.mention, inline=False)
            await basvuru_kanal.send(embed=embed)

# === KOMUTLAR ===
@bot.tree.command(name="selam", description="Selam verir")
async def slash_selam(interaction):
    await interaction.response.send_message(f"Selam {interaction.user.mention}!")

@bot.tree.command(name="ping", description="Bot gecikmesini gosterir")
async def slash_ping(interaction):
    await interaction.response.send_message(f"Pong! {round(bot.latency * 1000)}ms")

@bot.tree.command(name="kurallar", description="Sunucu kurallarini gosterir")
async def slash_kurallar(interaction):
    embed = discord.Embed(title="Sunucu Kurallari", color=discord.Color.blue())
    embed.add_field(name="1. Saygi", value="Herkes birbirine saygili davranmali.", inline=False)
    embed.add_field(name="2. Spam", value="Spam ve flood yapmak yasaktir.", inline=False)
    embed.add_field(name="3. Reklam", value="Izinsiz reklam yapmak yasaktir.", inline=False)
    embed.add_field(name="4. Uygunsuz Icerik", value="NSFW icerik paylasmak yasaktir.", inline=False)
    embed.add_field(name="5. Kural Ihlali", value="Kural ihlali yapanlar cezalandirilacaktir.", inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="paketler", description="Hizmet paketlerini gosterir")
async def slash_paketler(interaction):
    embed = discord.Embed(title="Hizmet Paketleri", color=discord.Color.gold())
    embed.add_field(name="Demir Paket", value=f"Temel ozellikler. Fiyat: {reklam_fiyatlari['demir']}TL", inline=False)
    embed.add_field(name="Altin Paket", value=f"Gelismis ozellikler. Fiyat: {reklam_fiyatlari['altin']}TL", inline=False)
    embed.add_field(name="Elmas Paket", value=f"Premium ozellikler. Fiyat: {reklam_fiyatlari['elmas']}TL", inline=False)
    embed.add_field(name="Netherite Paket", value=f"Tum ozellikler + VIP destek. Fiyat: {reklam_fiyatlari['netherite']}TL", inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="yardim", description="Tum komutlari gosterir")
async def slash_yardim(interaction):
    await interaction.response.send_message("""Komutlar:
/selam - Selam verir
/ping - Bot gecikmesini gosterir
/yardim - Bu mesaji gosterir
/kurallar - Sunucu kurallarini gosterir
/paketler - Hizmet paketlerini gosterir
/ilan-ver - Pazar alaninda ilan olusturur
/destek - Destek talebi olusturur
/lock - Kanali kilitler
/unlock - Kanal kilidini acar
/sil - Mesaj siler

Yonetici Komutlari:
/mesaj - Embed mesaj gonderir
/rol-basvuru - Rol basvuru paneli
/destek-panel - Destek paneli
/reklam-fiyat-ayarla - Reklam fiyatlarini ayarlar""")

@bot.tree.command(name="ilan-ver", description="Pazar alaninda ilan olusturur")
@app_commands.describe(urun="Urun adi", fiyat="Urun fiyati", aciklama="Urun aciklamasi")
async def slash_ilan_ver(interaction, urun: str, fiyat: str, aciklama: str):
    pazar_channel = interaction.guild.get_channel(PAZAR_KANAL_ID)
    if not pazar_channel:
        await interaction.response.send_message("Pazar alani kanali bulunamadi!", ephemeral=True)
        return
    embed = discord.Embed(title="Yeni Ilan", color=discord.Color.orange())
    embed.add_field(name="Ilan Sahibi", value=interaction.user.mention, inline=False)
    embed.add_field(name="Urun", value=urun, inline=True)
    embed.add_field(name="Fiyat", value=fiyat, inline=True)
    embed.add_field(name="Aciklama", value=aciklama, inline=False)
    await pazar_channel.send(embed=embed)
    await interaction.response.send_message("Ilaniniz pazar alanina gonderildi!", ephemeral=True)

@bot.tree.command(name="destek", description="Destek talebi olusturur")
async def slash_destek(interaction):
    await interaction.response.send_message("Destek talebi olusturmak icin /destek-panel komutunu kullanin.", ephemeral=True)

@bot.tree.command(name="lock", description="Kanali kilitler (Yetkili)")
@app_commands.checks.has_permissions(manage_channels=True)
async def slash_lock(interaction, kanal: discord.TextChannel = None):
    channel = kanal or interaction.channel
    await channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message(f"{channel.mention} kilitlendi!", ephemeral=True)

@slash_lock.error
async def slash_lock_error(interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("Yetkiniz yok!", ephemeral=True)

@bot.tree.command(name="unlock", description="Kanal kilidini acar (Yetkili)")
@app_commands.checks.has_permissions(manage_channels=True)
async def slash_unlock(interaction, kanal: discord.TextChannel = None):
    channel = kanal or interaction.channel
    await channel.set_permissions(interaction.guild.default_role, send_messages=True)
    await interaction.response.send_message(f"{channel.mention} acildi!", ephemeral=True)

@slash_unlock.error
async def slash_unlock_error(interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("Yetkiniz yok!", ephemeral=True)

@bot.tree.command(name="sil", description="Belirtilen sayida mesaj siler (Yetkili)")
@app_commands.checks.has_permissions(manage_messages=True)
@app_commands.describe(miktar="Silinecek mesaj sayisi (1-100)")
async def slash_sil(interaction, miktar: int):
    if miktar < 1 or miktar > 100:
        await interaction.response.send_message("1-100 arasi girin!", ephemeral=True)
        return
    await interaction.channel.purge(limit=miktar)
    await interaction.response.send_message(f"{miktar} mesaj silindi!", ephemeral=True)

@slash_sil.error
async def slash_sil_error(interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("Yetkiniz yok!", ephemeral=True)

@bot.tree.command(name="reklam-fiyat-ayarla", description="Reklam paket fiyatlarini ayarlar (Yetkili)")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(paket="Paket adi (demir, altin, elmas, netherite)", fiyat="Yeni fiyat")
async def slash_reklam_fiyat_ayarla(interaction, paket: str, fiyat: int):
    paket = paket.lower()
    if paket not in reklam_fiyatlari:
        await interaction.response.send_message("Gecersiz paket!", ephemeral=True)
        return
    reklam_fiyatlari[paket] = fiyat
    await interaction.response.send_message(f"{paket.capitalize()} Paket fiyati {fiyat}TL olarak guncellendi!", ephemeral=True)

@slash_reklam_fiyat_ayarla.error
async def slash_reklam_fiyat_ayarla_error(interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("Yetkiniz yok!", ephemeral=True)

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
    await interaction.response.send_message(f"Mesaj {kanal.mention} kanalina gonderildi!", ephemeral=True)

@slash_mesaj.error
async def slash_mesaj_error(interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("Yetkiniz yok!", ephemeral=True)

@bot.tree.command(name="rol-basvuru", description="Rol basvuru paneli olusturur (Yetkili)")
@app_commands.checks.has_permissions(administrator=True)
async def slash_rol_basvuru(interaction):
    embed = discord.Embed(title="Unvan Dogrulama Basvurulari", description="Sunucu sahibi, klan lideri, yayinci, hosting firmasi veya icerik ureticisi unvanlarina sahipseniz rollerinizi teslim almak icin asagidaki butona tiklayin.", color=discord.Color.purple())
    await interaction.response.send_message(embed=embed, view=RolBasvuruView())

@bot.tree.command(name="destek-panel", description="Destek paneli olusturur (Yetkili)")
@app_commands.checks.has_permissions(administrator=True)
async def slash_destek_panel(interaction):
    embed = discord.Embed(title="Destek Menusu", description="Asagidaki menuden destek talebi acabilirsiniz.\n\n- Yetkilileri mesgul etmek yasaktir.\n- Destek taleplerinizi kategorilere gore acin.\n- Uygun kanal secildikten sonra destek ekibi bilgilendirilecektir.", color=discord.Color.blurple())
    await interaction.response.send_message(embed=embed, view=TicketOlusturView())

@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name="genel-sohbet")
    if channel:
        embed = discord.Embed(title="Hos Geldin!", description=f"{member.mention} aramiza katildi! Hos geldin!", color=discord.Color.green())
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Toplam Uye", value=len(member.guild.members), inline=True)
        await channel.send(embed=embed)

@bot.event
async def on_member_remove(member):
    channel = discord.utils.get(member.guild.text_channels, name="genel-sohbet")
    if channel:
        embed = discord.Embed(title="Gule Gule!", description=f"{member.mention} aramizdan ayrildi. Gorusmek uzere!", color=discord.Color.red())
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Kalan Uye", value=len(member.guild.members), inline=True)
        await channel.send(embed=embed)

@bot.event
async def on_ready():
    print(f"{bot.user} aktif!")
    try:
        synced = await bot.tree.sync()
        print(f"{len(synced)} slash komutu senkronize edildi!")
    except Exception as e:
        print(f"Hata: {e}")

print("Bot baslatiliyor...")
bot.run(os.environ['DISCORD_TOKEN'])
