
new_main_py = '''import discord
from discord.ext import commands
from discord.ui import View, Button, Select, Modal, TextInput
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

# === DESTEK KATEGORİLERİ ===
DESTEK_KONULARI = {
    "partnerlik": "🤝 Partnerlik",
    "sikayet": "⚠️ Şikayet", 
    "yetkili-basvuru": "👮 Yetkili Başvuru",
    "reklam": "📢 Reklam",
    "genel": "❓ Genel"
}

# === ROL BAŞVURU BUTONLARI ===
class RolBasvuruView(View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="👑 Sunucu Sahibi", style=discord.ButtonStyle.primary, custom_id="rol_sunucu_sahibi")
    async def sunucu_sahibi(self, interaction: discord.Interaction, button: Button):
        await self.rol_basvuru_gonder(interaction, "Sunucu Sahibi")
    
    @discord.ui.button(label="⚔️ Klan Sahibi", style=discord.ButtonStyle.primary, custom_id="rol_klan_sahibi")
    async def klan_sahibi(self, interaction: discord.Interaction, button: Button):
        await self.rol_basvuru_gonder(interaction, "Klan Sahibi")
    
    @discord.ui.button(label="🎥 Yayıncı", style=discord.ButtonStyle.primary, custom_id="rol_yayinci")
    async def yayinci(self, interaction: discord.Interaction, button: Button):
        await self.rol_basvuru_gonder(interaction, "Yayıncı")
    
    @discord.ui.button(label="🖥️ Hosting Sahibi", style=discord.ButtonStyle.primary, custom_id="rol_hosting_sahibi")
    async def hosting_sahibi(self, interaction: discord.Interaction, button: Button):
        await self.rol_basvuru_gonder(interaction, "Hosting Sahibi")
    
    @discord.ui.button(label="📝 İçerik Üreticisi", style=discord.ButtonStyle.primary, custom_id="rol_icerik_ureticisi")
    async def icerik_ureticisi(self, interaction: discord.Interaction, button: Button):
        await self.rol_basvuru_gonder(interaction, "İçerik Üreticisi")
    
    async def rol_basvuru_gonder(self, interaction: discord.Interaction, rol_adi: str):
        modal = RolBasvuruModal(rol_adi)
        await interaction.response.send_modal(modal)

class RolBasvuruModal(Modal, title="Rol Başvuru Formu"):
    def __init__(self, rol_adi: str):
        super().__init__()
        self.rol_adi = rol_adi
        self.title = f"{rol_adi} Başvuru Formu"
    
    proje_adi = TextInput(label="Projenizin / Sunucunuzun Adı", placeholder="Örn: MinecraftTR", required=True)
    kanit = TextInput(label="Kanıt / Discord / Web Linki", placeholder="https://...", required=True)
    detay = TextInput(label="Eklemek istediğiniz detaylar", placeholder="Detaylı bilgi...", required=True, style=discord.TextStyle.paragraph)
    
    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=f"📝 {self.rol_adi} Başvurusu",
            color=discord.Color.gold()
        )
        embed.add_field(name="Başvuran", value=interaction.user.mention, inline=False)
        embed.add_field(name="Proje Adı", value=self.proje_adi.value, inline=False)
        embed.add_field(name="Kanıt/Link", value=self.kanit.value, inline=False)
        embed.add_field(name="Detaylar", value=self.detay.value, inline=False)
        embed.set_footer(text=f"Başvuru Tarihi: {discord.utils.utcnow().strftime('%d/%m/%Y %H:%M')}")
        
        # Başvuru kanalına gönder
        basvuru_kanal = discord.utils.get(interaction.guild.text_channels, name="basvurular")
        if basvuru_kanal:
            await basvuru_kanal.send(embed=embed)
        
        await interaction.response.send_message(f"✅ {self.rol_adi} başvurunuz alındı! En kısa sürede incelenecektir.", ephemeral=True)

# === DESTEK MODAL ===
class DestekModal(Modal, title="Destek Talebi"):
    konu = TextInput(label="Konu başlığı", placeholder="Örn: reklam başvurusu, partnerlik isteği...", required=True)
    detay = TextInput(label="Detaylı açıklama", placeholder="Sorununuzu detaylıca anlatın...", required=True, style=discord.TextStyle.paragraph)
    
    async def on_submit(self, interaction: discord.Interaction):
        # Ticket kanalı oluştur
        support_rol = interaction.guild.get_role(1524866585637031961)
        
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        if support_rol:
            overwrites[support_rol] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        
        channel = await interaction.guild.create_text_channel(
            name=f"destek-{interaction.user.name}",
            overwrites=overwrites
        )
        
        embed = discord.Embed(
            title=f"🎫 Destek Talebi: {self.konu.value}",
            description=f"{interaction.user.mention} tarafından oluşturuldu.\\n\\n**Detay:**\\n{self.detay.value}",
            color=discord.Color.green()
        )
        embed.add_field(name="Kategori", value="Destek", inline=True)
        embed.add_field(name="Kullanıcı", value=interaction.user.mention, inline=True)
        embed.add_field(name="Kullanıcı ID", value=interaction.user.id, inline=True)
        embed.set_footer(text=f"Açılış Zamanı: {discord.utils.utcnow().strftime('%d/%m/%Y %H:%M')}")
        
        if support_rol:
            await channel.send(f"{support_rol.mention} Yeni destek talebi!", embed=embed)
        else:
            await channel.send(embed=embed)
        
        # Kapat butonu
        kapat_view = View(timeout=None)
        kapat_btn = Button(label="Talebi Kapat", style=discord.ButtonStyle.danger, custom_id="kapat_ticket")
        
        async def kapat_callback(interaction2: discord.Interaction):
            if interaction2.user.guild_permissions.administrator or (support_rol and support_rol in interaction2.user.roles):
                await interaction2.response.send_message("🔒 Ticket 5 saniye sonra kapatılacak...")
                await asyncio.sleep(5)
                await interaction2.channel.delete()
            else:
                await interaction2.response.send_message("❌ Bu işlem için yetkiniz yok!", ephemeral=True)
        
        kapat_btn.callback = kapat_callback
        kapat_view.add_item(kapat_btn)
        
        await channel.send(view=kapat_view)
        await interaction.response.send_message(f"✅ Destek talebiniz açıldı: {channel.mention}", ephemeral=True)

# === DESTEK KATEGORİ SELECT ===
class DestekView(View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.select(
        placeholder="Destek konusu seçin...",
        options=[
            discord.SelectOption(label="🤝 Partnerlik", value="partnerlik", description="Partnerlik başvurusu"),
            discord.SelectOption(label="⚠️ Şikayet", value="sikayet", description="Bir şikayet bildirin"),
            discord.SelectOption(label="👮 Yetkili Başvuru", value="yetkili-basvuru", description="Yetkili ekibine katılın"),
            discord.SelectOption(label="📢 Reklam", value="reklam", description="Reklam başvurusu"),
            discord.SelectOption(label="❓ Genel", value="genel", description="Genel destek talebi")
        ],
        custom_id="destek_kategori"
    )
    async def destek_select(self, interaction: discord.Interaction, select: Select):
        modal = DestekModal()
        modal.title = f"{DESTEK_KONULARI[select.values[0]]} Talebi"
        await interaction.response.send_modal(modal)

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
`/destek` - Destek talebi oluşturur

**👑 Yönetici Komutları:**
`/mesaj` - Belirtilen kanala embed mesaj gönderir
`/rol-basvuru` - Rol başvuru paneli oluşturur
`/destek-panel` - Destek paneli oluşturur"""
    await interaction.response.send_message(help_text)

@bot.tree.command(name="ilan-ver", description="Pazar alanında ilan oluşturur")
@discord.app_commands.describe(urun="Ürün adı", fiyat="Ürün fiyatı", aciklama="Ürün açıklaması")
async def slash_ilan_ver(interaction: discord.Interaction, urun: str, fiyat: str, aciklama: str):
    # Belirtilen kanal ID'sini kullan
    pazar_channel = bot.get_channel(1524866586912227330)
    if not pazar_channel:
        await interaction.response.send_message("❌ Pazar alanı kanalı bulunamadı!", ephemeral=True)
        return
    
    embed = discord.Embed(title="🛒 Yeni İlan", color=discord.Color.orange())
    embed.add_field(name="İlan Sahibi", value=interaction.user.mention, inline=False)
    embed.add_field(name="Ürün", value=urun, inline=True)
    embed.add_field(name="Fiyat", value=fiyat, inline=True)
    embed.add_field(name="Açıklama", value=aciklama, inline=False)
    embed.set_footer(text=f"İlan Tarihi: {discord.utils.utcnow().strftime('%d/%m/%Y')}")
    
    await pazar_channel.send(embed=embed)
    await interaction.response.send_message(f"✅ İlanınız pazar alanına gönderildi!", ephemeral=True)

@bot.tree.command(name="destek", description="Destek talebi oluşturur")
async def slash_destek(interaction: discord.Interaction):
    modal = DestekModal()
    await interaction.response.send_modal(modal)

@bot.tree.command(name="mesaj", description="Belirtilen kanala embed mesaj gönderir (Yetkili)")
@discord.app_commands.checks.has_permissions(administrator=True)
@discord.app_commands.describe(kanal="Mesajın gönderileceği kanal", baslik="Mesaj başlığı", mesaj="Gönderilecek mesaj", renk="Embed rengi (kirmizi, yesil, mavi, sari, mor)")
async def slash_mesaj(interaction: discord.Interaction, kanal: discord.TextChannel, mesaj: str, baslik: str = None, renk: str = "mavi"):
    renkler = {
        "kirmizi": discord.Color.red(),
        "yesil": discord.Color.green(),
        "mavi": discord.Color.blue(),
        "sari": discord.Color.gold(),
        "mor": discord.Color.purple()
    }
    
    embed = discord.Embed(
        description=mesaj,
        color=renkler.get(renk.lower(), discord.Color.blue())
    )
    if baslik:
        embed.title = baslik
    embed.set_footer(text=f"Gönderen: {interaction.user.display_name}")
    embed.timestamp = discord.utils.utcnow()
    
    await kanal.send(embed=embed)
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
        description="Sunucu sahibi, klan lideri, yayıncı, hosting firması veya içerik üreticisi unvanlarına sahipseniz rollerinizi teslim almak için aşağıdaki butona tıklayın.",
        color=discord.Color.purple()
    )
    await interaction.response.send_message(embed=embed, view=RolBasvuruView())

@bot.tree.command(name="destek-panel", description="Destek paneli oluşturur (Yetkili)")
@discord.app_commands.checks.has_permissions(administrator=True)
async def slash_destek_panel(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎫 Destek Sistemi",
        description="Destek talebi oluşturmak için aşağıdaki menüden konusunu seçin.",
        color=discord.Color.blurple()
    )
    await interaction.response.send_message(embed=embed, view=DestekView())

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
'''

print("Kod hazırlandı!")
print(f"Kod uzunluğu: {len(new_main_py)} karakter")
