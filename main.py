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

# === KURALLAR ===
@bot.command()
async def kurallar(ctx):
    embed = discord.Embed(title="📜 Sunucu Kuralları", color=discord.Color.blue())
    embed.add_field(name="1. Saygı", value="Herkes birbirine saygılı davranmalı.", inline=False)
    embed.add_field(name="2. Spam", value="Spam ve flood yapmak yasaktır.", inline=False)
    embed.add_field(name="3. Reklam", value="İzinsiz reklam yapmak yasaktır.", inline=False)
    embed.add_field(name="4. Uygunsuz İçerik", value="NSFW içerik paylaşmak yasaktır.", inline=False)
    embed.add_field(name="5. Kural İhlali", value="Kural ihlali yapanlar cezalandırılacaktır.", inline=False)
    await ctx.send(embed=embed)

# === PAKETLER ===
@bot.command()
async def paketler(ctx):
    embed = discord.Embed(title="💎 Hizmet Paketleri", description="Sunucumuzun hizmet paketlerini inceleyin.", color=discord.Color.gold())
    embed.add_field(name="🔩 Demir Paket", value="Temel özellikler. Fiyat: 50₺", inline=False)
    embed.add_field(name="🥇 Altın Paket", value="Gelişmiş özellikler. Fiyat: 100₺", inline=False)
    embed.add_field(name="💎 Elmas Paket", value="Premium özellikler. Fiyat: 200₺", inline=False)
    embed.add_field(name="⚔️ Netherite Paket", value="Tüm özellikler + VIP destek. Fiyat: 500₺", inline=False)
    embed.set_footer(text="Paket satın almak için yöneticilere ulaşın.")
    await ctx.send(embed=embed)

# === İLAN VER ===
@bot.command()
async def ilan_ver(ctx, urun: str, fiyat: str, *, aciklama: str):
    pazar_channel = discord.utils.get(ctx.guild.text_channels, name="pazar-alani")
    if not pazar_channel:
        await ctx.send("❌ pazar-alani kanalı bulunamadı!")
        return
    embed = discord.Embed(title="🛒 Yeni İlan", color=discord.Color.orange())
    embed.add_field(name="İlan Sahibi", value=ctx.author.mention, inline=False)
    embed.add_field(name="Ürün", value=urun, inline=True)
    embed.add_field(name="Fiyat", value=fiyat, inline=True)
    embed.add_field(name="Açıklama", value=aciklama, inline=False)
    embed.set_footer(text=f"İlan Tarihi: {ctx.message.created_at.strftime('%d/%m/%Y')}")
    await pazar_channel.send(embed=embed)
    await ctx.send(f"✅ İlanınız {pazar_channel.mention} kanalına gönderildi!")

# === DESTEK / TICKET ===
@bot.command()
@commands.has_permissions(administrator=True)
async def destek_panel(ctx):
    embed = discord.Embed(title="🎫 Destek Sistemi", description="Destek talebi oluşturmak için `!ticket <konu>` yazın.", color=discord.Color.blurple())
    await ctx.send(embed=embed)

@bot.command()
async def ticket(ctx, *, konu: str = "Destek Talebi"):
    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        ctx.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }
    yetkili_rol = discord.utils.get(ctx.guild.roles, name="Yetkili") or discord.utils.get(ctx.guild.roles, name="Admin")
    if yetkili_rol:
        overwrites[yetkili_rol] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
    
    channel = await ctx.guild.create_text_channel(name=f"ticket-{ctx.author.name}", overwrites=overwrites, category=ctx.channel.category)
    embed = discord.Embed(title=f"🎫 {konu}", description=f"{ctx.author.mention} tarafından oluşturuldu.\n\nYardımcı olabilmemiz için sorununuzu detaylıca anlatın.", color=discord.Color.green())
    embed.set_footer(text="Ticket kapatmak için yetkili !kapat yazsın.")
    await channel.send(embed=embed)
    await ctx.send(f"✅ Ticket oluşturuldu: {channel.mention}")

@bot.command()
@commands.has_permissions(administrator=True)
async def kapat(ctx):
    if ctx.channel.name.startswith("ticket-"):
        await ctx.send("🔒 Ticket 5 saniye sonra kapatılacak...")
        await asyncio.sleep(5)
        await ctx.channel.delete()
    else:
        await ctx.send("❌ Bu komut sadece ticket kanallarında kullanılabilir!")

# === YÖNETİCİ MESAJ ===
@bot.command()
@commands.has_permissions(administrator=True)
async def mesaj(ctx, kanal: discord.TextChannel, *, mesaj_icerik: str):
    await kanal.send(mesaj_icerik)
    await ctx.send(f"✅ Mesaj {kanal.mention} kanalına gönderildi!")

@mesaj.error
async def mesaj_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Bu komutu kullanmak için yönetici yetkisine sahip olmalısınız!")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ Kanal bulunamadı! Doğru kanal etiketini kullanın. (Örn: #kanal)")

# === ROL BAŞVURU ===
@bot.command()
@commands.has_permissions(administrator=True)
async def rol_basvuru(ctx):
    embed = discord.Embed(title="👑 Ünvan Doğrulama Başvuruları", description="Sunucu sahibi, klan lideri, yayıncı veya hosting firması unvanlarına sahipseniz rollerinizi teslim almak için başvurun.", color=discord.Color.purple())
    await ctx.send(embed=embed)

# === TEMEL KOMUTLAR ===
@bot.command()
async def selam(ctx):
    await ctx.send(f"Selam {ctx.author.mention}! 👋")

@bot.command()
async def ping(ctx):
    await ctx.send(f"Pong! 🏓 Gecikme: {round(bot.latency * 1000)}ms")

@bot.command()
async def yardim(ctx):
    help_text = """**📋 Komutlar:**
`!selam` - Selam verir
`!ping` - Bot gecikmesini gösterir
`!yardim` - Bu mesajı gösterir
`!kurallar` - Sunucu kurallarını gösterir
`!paketler` - Hizmet paketlerini gösterir
`!ilan-ver <ürün> <fiyat> <açıklama>` - Pazar alanında ilan oluşturur
`!ticket <konu>` - Destek talebi oluşturur

**👑 Yönetici Komutları:**
`!mesaj #kanal <mesaj>` - Belirtilen kanala mesaj gönderir
`!rol_basvuru` - Rol başvuru paneli oluşturur
`!destek_panel` - Destek paneli oluşturur
`!kapat` - Ticket kanalını kapatır"""
    await ctx.send(help_text)

@bot.event
async def on_ready():
    print(f"✅ {bot.user} aktif!")

print("Bot başlatılıyor...")
bot.run(os.environ['DISCORD_TOKEN'])
