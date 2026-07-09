import discord
from discord.ext import commands
from discord import app_commands
import os
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

@bot.tree.command(name="selam", description="Selam verir")
async def slash_selam(interaction):
    await interaction.response.send_message(f"Selam {interaction.user.mention}! 👋")

@bot.tree.command(name="ping", description="Bot gecikmesini gösterir")
async def slash_ping(interaction):
    await interaction.response.send_message(f"Pong! 🏓 Gecikme: {round(bot.latency * 1000)}ms")

@bot.tree.command(name="kurallar", description="Sunucu kurallarını gösterir")
async def slash_kurallar(interaction):
    embed = discord.Embed(title="📜 Sunucu Kuralları", color=discord.Color.blue())
    embed.add_field(name="1. Saygı", value="Herkes birbirine saygılı davranmalı.", inline=False)
    embed.add_field(name="2. Spam", value="Spam ve flood yapmak yasaktır.", inline=False)
    embed.add_field(name="3. Reklam", value="İzinsiz reklam yapmak yasaktır.", inline=False)
    embed.add_field(name="4. Uygunsuz İçerik", value="NSFW içerik paylaşmak yasaktır.", inline=False)
    embed.add_field(name="5. Kural İhlali", value="Kural ihlali yapanlar cezalandırılacaktır.", inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="paketler", description="Hizmet paketlerini gösterir")
async def slash_paketler(interaction):
    embed = discord.Embed(title="💎 Hizmet Paketleri", color=discord.Color.gold())
    embed.add_field(name="🔩 Demir Paket", value=f"Temel özellikler. Fiyat: {reklam_fiyatlari['demir']}₺", inline=False)
    embed.add_field(name="🥇 Altın Paket", value=f"Gelişmiş özellikler. Fiyat: {reklam_fiyatlari['altin']}₺", inline=False)
    embed.add_field(name="💎 Elmas Paket", value=f"Premium özellikler. Fiyat: {reklam_fiyatlari['elmas']}₺", inline=False)
    embed.add_field(name="⚔️ Netherite Paket", value=f"Tüm özellikler + VIP destek. Fiyat: {reklam_fiyatlari['netherite']}₺", inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="yardim", description="Tüm komutları gösterir")
async def slash_yardim(interaction):
    await interaction.response.send_message("""**📋 Komutlar:**
`/selam` - Selam verir
`/ping` - Bot gecikmesini gösterir
`/yardim` - Bu mesajı gösterir
`/kurallar` - Sunucu kurallarını gösterir
`/paketler` - Hizmet paketlerini gösterir
`/ilan-ver` - Pazar alanında ilan oluşturur
`/lock` - Kanalı kilitler
`/unlock` - Kanal kilidini açar
`/sil` - Mesaj siler""")

@bot.tree.command(name="ilan-ver", description="Pazar alanında ilan oluşturur")
@app_commands.describe(urun="Ürün adı", fiyat="Ürün fiyatı", aciklama="Ürün açıklaması")
async def slash_ilan_ver(interaction, urun: str, fiyat: str, aciklama: str):
    pazar_channel = interaction.guild.get_channel(PAZAR_KANAL_ID)
    if not pazar_channel:
        await interaction.response.send_message("❌ Pazar alanı kanalı bulunamadı!", ephemeral=True)
        return
    embed = discord.Embed(title="🛒 Yeni İlan", color=discord.Color.orange())
    embed.add_field(name="İlan Sahibi", value=interaction.user.mention, inline=False)
    embed.add_field(name="Ürün", value=urun, inline=True)
    embed.add_field(name="Fiyat", value=fiyat, inline=True)
    embed.add_field(name="Açıklama", value=aciklama, inline=False)
    await pazar_channel.send(embed=embed)
    await interaction.response.send_message("✅ İlanınız pazar alanına gönderildi!", ephemeral=True)

@bot.tree.command(name="lock", description="Kanalı kilitler (Yetkili)")
@app_commands.checks.has_permissions(manage_channels=True)
async def slash_lock(interaction, kanal: discord.TextChannel = None):
    channel = kanal or interaction.channel
    await channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message(f"🔒 {channel.mention} kilitlendi!", ephemeral=True)

@slash_lock.error
async def slash_lock_error(interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Yetkiniz yok!", ephemeral=True)

@bot.tree.command(name="unlock", description="Kanal kilidini açar (Yetkili)")
@app_commands.checks.has_permissions(manage_channels=True)
async def slash_unlock(interaction, kanal: discord.TextChannel = None):
    channel = kanal or interaction.channel
    await channel.set_permissions(interaction.guild.default_role, send_messages=True)
    await interaction.response.send_message(f"🔓 {channel.mention} açıldı!", ephemeral=True)

@slash_unlock.error
async def slash_unlock_error(interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Yetkiniz yok!", ephemeral=True)

@bot.tree.command(name="sil", description="Belirtilen sayıda mesaj siler (Yetkili)")
@app_commands.checks.has_permissions(manage_messages=True)
@app_commands.describe(miktar="Silinecek mesaj sayısı (1-100)")
async def slash_sil(interaction, miktar: int):
    if miktar < 1 or miktar > 100:
        await interaction.response.send_message("❌ 1-100 arası girin!", ephemeral=True)
        return
    await interaction.channel.purge(limit=miktar)
    await interaction.response.send_message(f"🗑️ {miktar} mesaj silindi!", ephemeral=True)

@slash_sil.error
async def slash_sil_error(interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Yetkiniz yok!", ephemeral=True)

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
    await interaction.response.send_message(f"✅ Mesaj {kanal.mention} kanalına gönderildi!", ephemeral=True)

@slash_mesaj.error
async def slash_mesaj_error(interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Yetkiniz yok!", ephemeral=True)

@bot.tree.command(name="reklam-fiyat-ayarla", description="Reklam paket fiyatlarını ayarlar (Yetkili)")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(paket="Paket adı (demir, altin, elmas, netherite)", fiyat="Yeni fiyat")
async def slash_reklam_fiyat_ayarla(interaction, paket: str, fiyat: int):
    paket = paket.lower()
    if paket not in reklam_fiyatlari:
        await interaction.response.send_message("❌ Geçersiz paket!", ephemeral=True)
        return
    reklam_fiyatlari[paket] = fiyat
    await interaction.response.send_message(f"✅ {paket.capitalize()} Paket fiyatı {fiyat}₺ olarak güncellendi!", ephemeral=True)

@slash_reklam_fiyat_ayarla.error
async def slash_reklam_fiyat_ayarla_error(interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Yetkiniz yok!", ephemeral=True)

@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name="genel-sohbet")
    if channel:
        embed = discord.Embed(title="🎉 Hoş Geldin!", description=f"{member.mention} aramıza katıldı! Hoş geldin!", color=discord.Color.green())
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Toplam Üye", value=len(member.guild.members), inline=True)
        await channel.send(embed=embed)

@bot.event
async def on_member_remove(member):
    channel = discord.utils.get(member.guild.text_channels, name="genel-sohbet")
    if channel:
        embed = discord.Embed(title="👋 Güle Güle!", description=f"{member.mention} aramızdan ayrıldı. Görüşmek üzere!", color=discord.Color.red())
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Kalan Üye", value=len(member.guild.members), inline=True)
        await channel.send(embed=embed)

@bot.event
async def on_ready():
    print(f"✅ {bot.user} aktif!")
    try:
        synced = await bot.tree.sync()
        print(f"🔄 {len(synced)} slash komutu senkronize edildi!")
    except Exception as e:
        print(f"❌ Hata: {e}")

print("Bot başlatılıyor...")
bot.run(os.environ['DISCORD_TOKEN'])
