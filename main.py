import discord
from discord.ext import commands
import os
import asyncio
from flask import Flask
from threading import Thread

# === WEB SERVER ===
app = Flask('')

@app.route('/')
def home():
    return "Bot aktif! 🚀"

def run_web():
    app.run(host='0.0.0.0', port=8080)

Thread(target=run_web, daemon=True).start()

# === DISCORD BOT ===
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# === SLASH COMMANDS ===

@bot.tree.command(name="selam", description="Selam verir")
async def slash_selam(interaction: discord.Interaction):
    await interaction.response.send_message(f"Selam {interaction.user.mention}! 👋")

@bot.tree.command(name="ping", description="Bot gecikmesini gösterir")
async def slash_ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong! 🏓 Gecikme: {round(bot.latency * 1000)}ms")

@bot.tree.command(name="kurallar", description="Sunucu kurallarını gösterir")
async def slash_kurallar(interaction: discord.Interaction):
    embed = discord.Embed(title="📜 Sunucu Kuralları", color=discord.Color.blue())
    embed.add_field(name="1. Saygı", value="Herkes birbirine saygılı davranmalı.", inline=False)
    embed.add_field(name="2. Spam", value="Spam ve flood yapmak yasaktır.", inline=False)
    embed.add_field(name="3. Reklam", value="İzinsiz reklam yapmak yasaktır.", inline=False)
    embed.add_field(name="4. Uygunsuz İçerik", value="NSFW içerik paylaşmak yasaktır.", inline=False)
    embed.add_field(name="5. Kural İhlali", value="Kural ihlali yapanlar cezalandırılacaktır.", inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="paketler", description="Hizmet paketlerini gösterir")
async def slash_paketler(interaction: discord.Interaction):
    embed = discord.Embed(title="💎 Hizmet Paketleri", description="Sunucumuzun hizmet paketlerini inceleyin.", color=discord.Color.gold())
    embed.add_field(name="🔩 Demir Paket", value="Temel özellikler. Fiyat: 50₺", inline=False)
    embed.add_field(name="🥇 Altın Paket", value="Gelişmiş özellikler. Fiyat: 100₺", inline=False)
    embed.add_field(name="💎 Elmas Paket", value="Premium özellikler. Fiyat: 200₺", inline=False)
    embed.add_field(name="⚔️ Netherite Paket", value="Tüm özellikler + VIP destek. Fiyat: 500₺", inline=False)
    embed.set_footer(text="Paket satın almak için yöneticilere ulaşın.")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="yardim", description="Tüm komutları gösterir")
async def slash_yardim(interaction: discord.Interaction):
    help_text = """**📋 Slash Komutlar:**
`/selam` - Selam verir
`/ping` - Bot gecikmesini gösterir
`/yardim` - Bu mesajı gösterir
`/kurallar` - Sunucu kurallarını gösterir
`/paketler` - Hizmet paketlerini gösterir
`/ilan-ver` - Pazar alanında ilan oluşturur
`/ticket` - Destek talebi oluşturur

**👑 Yönetici Komutları:**
`/mesaj` - Belirtilen kanala mesaj gönderir
`/rol-basvuru` - Rol başvuru paneli oluşturur
`/destek-panel` - Destek paneli oluşturur
`/kapat` - Ticket kanalını kapatır"""
    await interaction.response.send_message(help_text)

@bot.tree.command(name="ilan-ver", description="Pazar alanında ilan oluşturur")
@discord.app_commands.describe(urun="Ürün adı", fiyat="Ürün fiyatı", aciklama="Ürün açıklaması")
async def slash_ilan_ver(interaction: discord.Interaction, urun: str, fiyat: str, aciklama: str):
    pazar_channel = discord.utils.get(interaction.guild.text_channels, name="pazar-alani")
    if not pazar_channel:
        await interaction.response.send_message("❌ pazar-alani kanalı bulunamadı!", ephemeral=True)
        return
    
    embed = discord.Embed(title="🛒 Yeni İlan", color=discord.Color.orange())
    embed.add_field(name="İlan Sahibi", value=interaction.user.mention, inline=False)
    embed.add_field(name="Ürün", value=urun, inline=True)
    embed.add_field(name="Fiyat", value=fiyat, inline=True)
    embed.add_field(name="Açıklama", value=aciklama, inline=False)
    embed.set_footer(text=f"İlan Tarihi: {discord.utils.utcnow().strftime('%d/%m/%Y')}")
    
    await pazar_channel.send(embed=embed)
    await interaction.response.send_message(f"✅ İlanınız {pazar_channel.mention} kanalına gönderildi!", ephemeral=True)

@bot.tree.command(name="ticket", description="Destek talebi oluşturur")
@discord.app_commands.describe(konu="Destek konusu")
async def slash_ticket(interaction: discord.Interaction, konu: str = "Destek Talebi"):
    overwrites = {
        interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }
    yetkili_rol = discord.utils.get(interaction.guild.roles, name="Yetkili") or discord.utils.get(interaction.guild.roles, name="Admin")
    if yetkili_rol:
        overwrites[yetkili_rol] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
    
    channel = await interaction.guild.create_text_channel(
        name=f"ticket-{interaction.user.name}",
        overwrites=overwrites,
        category=interaction.channel.category
    )
    
    embed = discord.Embed(
        title=f"🎫 {konu}",
        description=f"{interaction.user.mention} tarafından oluşturuldu.\n\nYardımcı olabilmemiz için sorununuzu detaylıca anlatın.",
        color=discord.Color.green()
    )
    embed.set_footer(text="Ticket kapatmak için yetkili /kapat yazsın.")
    await channel.send(embed=embed)
    await interaction.response.send_message(f"✅ Ticket oluşturuldu: {channel.mention}", ephemeral=True)

@bot.tree.command(name="kapat", description="Ticket kanalını kapatır (Yetkili)")
@discord.app_commands.checks.has_permissions(administrator=True)
async def slash_kapat(interaction: discord.Interaction):
    if interaction.channel.name.startswith("ticket-"):
        await interaction.response.send_message("🔒 Ticket 5 saniye sonra kapatılacak...")
        await asyncio.sleep(5)
        await interaction.channel.delete()
    else:
        await interaction.response.send_message("❌ Bu komut sadece ticket kanallarında kullanılabilir!", ephemeral=True)

@slash_kapat.error
async def slash_kapat_error(interaction: discord.Interaction, error):
    if isinstance(error, discord.app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Bu komutu kullanmak için yönetici yetkisine sahip olmalısınız!", ephemeral=True)

@bot.tree.command(name="mesaj", description="Belirtilen kanala mesaj gönderir (Yetkili)")
@discord.app_commands.checks.has_permissions(administrator=True)
@discord.app_commands.describe(kanal="Mesajın gönderileceği kanal", mesaj="Gönderilecek mesaj")
async def slash_mesaj(interaction: discord.Interaction, kanal: discord.TextChannel, mesaj: str):
    await kanal.send(mesaj)
    await interaction.response.send_message(f"✅ Mesaj {kanal.mention} kanalına gönderildi!", ephemeral=True)

@slash_mesaj.error
async def slash_mesaj_error(interaction: discord.Interaction, error):
    if isinstance(error, discord.app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Bu komutu kullanmak için yönetici yetkisine sahip olmalısınız!", ephemeral=True)

@bot.tree.command(name="rol-basvuru", description="Rol başvuru paneli oluşturur (Yetkili)")
@discord.app_commands.checks.has_permissions(administrator=True)
async def slash_rol_basvuru(interaction: discord.Interaction):
    embed = discord.Embed(
        title="👑 Ünvan Doğrulama Başvuruları",
        description="Sunucu sahibi, klan lideri, yayıncı veya hosting firması unvanlarına sahipseniz rollerinizi teslim almak için başvurun.",
        color=discord.Color.purple()
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="destek-panel", description="Destek paneli oluşturur (Yetkili)")
@discord.app_commands.checks.has_permissions(administrator=True)
async def slash_destek_panel(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎫 Destek Sistemi",
        description="Destek talebi oluşturmak için `/ticket <konu>` yazın.",
        color=discord.Color.blurple()
    )
    await interaction.response.send_message(embed=embed)

# === HOŞ GELDİN ===
@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name="genel-sohbet")
    if channel:
        embed = discord.Embed(
            title="🎉 Hoş Geldin!",
            description=f"{member.mention} aramıza katıldı! Hoş geldin!",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Toplam Üye", value=len(member.guild.members), inline=True)
        await channel.send(embed=embed)

@bot.event
async def on_ready():
    print(f"✅ {bot.user} aktif!")
    try:
        synced = await bot.tree.sync()
        print(f"🔄 {len(synced)} slash komutu senkronize edildi!")
    except Exception as e:
        print(f"❌ Slash komutları senkronize edilemedi: {e}")

# BOTU BAŞLAT
print("Bot başlatılıyor...")
bot.run(os.environ['DISCORD_TOKEN'])
