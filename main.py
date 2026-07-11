import discord
import os
from discord import app_commands
from discord.ui import Select, Modal, TextInput, View
from discord.ext import commands
from threading import Thread
from flask import Flask

# === AYARLAR VE KANAL ID'LERİ ===
BAŞVURU_LOG_KANAL_ID = 1524879141793435689
GIRIS_CIKIS_KANAL_ID = 123456789012345678  # 👈 Giriş-Çıkış loglarının atılacağı kanal ID'sini buraya gir!

ROL_SUNUCU_SAHIBI = 123456789012345678
ROL_KLAN_SAHIBI = 123456789012345678
ROL_HOSTING_SAHIBI = 123456789012345678
ROL_ICERIK_URETICISI = 123456789012345678

# === RENDER KEEPALIVE SİSTEMİ ===
app = Flask('')

@app.route('/')
def home():
    return "MTTS Bot Aktif!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web)
    t.start()

# === BOT AYARLARI ===
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True # Giriş-Çıkış olaylarını yakalamak için kesinlikle True olmalı
bot = commands.Bot(command_prefix="!", intents=intents)

# === GİRİŞ VE ÇIKIŞ (HOŞ GELDİN / GÜLE GÜLE) SİSTEMİ ===
@bot.event
async def on_member_join(member):
    channel = member.guild.get_channel(GIRIS_CIKIS_KANAL_ID)
    if channel:
        embed = discord.Embed(
            description=f"{member.mention} aramıza hoş geldin! **{member.guild.member_count}** kişiyiz.",
            color=discord.Color.from_rgb(46, 204, 113) # Canlı Yeşil (Fotoğraftaki gibi)
        )
        embed.set_author(name="📥 Sunucuya Katıldı!")
        embed.set_thumbnail(url=member.display_avatar.url) # Katılan kullanıcının profil fotoğrafını sağa koyar
        await channel.send(embed=embed)

@bot.event
async def on_member_remove(member):
    channel = member.guild.get_channel(GIRIS_CIKIS_KANAL_ID)
    if channel:
        embed = discord.Embed(
            description=f"**{member.name}** aramızdan ayrıldı. **{member.guild.member_count}** kişi kaldık.",
            color=discord.Color.from_rgb(231, 76, 60) # Canlı Kırmızı
        )
        embed.set_author(name="📤 Sunucudan Ayrıldı!")
        embed.set_thumbnail(url=member.display_avatar.url)
        await channel.send(embed=embed)

# === YENİ GELİŞMİŞ DESTEK KANALI İÇİ BUTONLARI ===
class DestekKanalIciView(View):
    def __init__(self):
        super().__init__(timeout=None)
        
    @discord.ui.button(label="Kapat", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="ticket_kapat_btn_yeni")
    async def ticket_kapat(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.defer()
        await interaction.channel.send("🔒 Bu destek talebi 5 saniye içinde kapatılıyor...")
        await discord.utils.sleep_until(discord.utils.utcnow() + discord.utils.datetime.timedelta(seconds=5))
        await interaction.channel.delete()

    @discord.ui.button(label="Aktif Yetkililer", style=discord.ButtonStyle.primary, emoji="👤", custom_id="ticket_aktif_yetkililer")
    async def aktif_yetkililer(self, interaction: discord.Interaction, button: discord.Button):
        online_staff = [m.mention for m in interaction.guild.members if not m.bot and m.guild_permissions.manage_messages and m.status != discord.Status.offline]
        mentions = ", ".join(online_staff[:5]) if online_staff else "Şu an aktif yetkili bulunamadı."
        await interaction.response.send_message(f"🔔 **Aktif Yetkililer Bilgilendirildi:** {mentions}", ephemeral=True)

    @discord.ui.button(label="Yardım Al", style=discord.ButtonStyle.success, emoji="🆘", custom_id="ticket_yardim_al")
    async def yardim_al(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.send_message("🚨 Destek ekibine acil çağrı gönderildi! En kısa sürede odaklanacaklar.", ephemeral=False)

# === KISACA SORUNUNUZU BİLDİRİN FORMU (MODAL) ===
class DestekSorunuModal(Modal):
    def __init__(self, kategori: str):
        super().__init__(title=f"{kategori.capitalize()} Destek Formu")
        self.kategori = kategori
        
        self.sorun = TextInput(
            label="Kısaca Sorununuzu Bildirin", 
            placeholder="Lütfen talebinizin nedenini buraya kısaca yazın...", 
            style=discord.TextStyle.paragraph,
            required=True
        )
        self.add_item(self.sorun)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        member = interaction.user
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        for role in guild.roles:
            if role.permissions.administrator:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        kanal_adi = f"{self.kategori}-{member.name}".lower()
        ticket_channel = await guild.create_text_channel(name=kanal_adi, overwrites=overwrites)
        
        embed = discord.Embed(title="📋 Destek Talebi", color=discord.Color.from_rgb(41, 128, 185))
        embed.description = "Destek ekibimiz en kısa sürede size yardımcı olacaktır."
        
        embed.add_field(name="📌 Konu", value=self.sorun.value, inline=False)
        embed.add_field(name="📁 Kategori", value=self.kategori, inline=True)
        embed.add_field(name="👤 Kullanıcı", value=f"{member.name}", inline=True)
        embed.add_field(name="🆔 Kullanıcı ID", value=f"{member.id}", inline=True)
        
        zaman_str = discord.utils.utcnow().strftime('%d %B %Y %H:%M')
        embed.add_field(name="⏳ Açılış Zamanı", value=zaman_str, inline=False)
        embed.set_footer(text=f"Ticket ID: {ticket_channel.id} • {discord.utils.utcnow().strftime('%d.%m.%Y %H:%M')}")
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        await ticket_channel.send(content=f"{member.mention}, destek talebiniz açıldı.", embed=embed, view=DestekKanalIciView())
        await interaction.followup.send(f"✅ Destek talebiniz başarıyla oluşturuldu: {ticket_channel.mention}", ephemeral=True)

# === DROPDOWN (AÇIRLIR MENÜ) TASARIMI ===
class DestekDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Partnerlik", value="partnerlik", emoji="📄"),
            discord.SelectOption(label="Şikayet", value="sikayet", emoji="🚨"),
            discord.SelectOption(label="Yetkili Başvurusu", value="yetkili", emoji="📁"),
            discord.SelectOption(label="Reklam", value="reklam", emoji="💵"),
            discord.SelectOption(label="Genel", value="genel", emoji="📜")
        ]
        super().__init__(placeholder="📌 Bir destek kategorisi seçin", min_values=1, max_values=1, options=options, custom_id="destek_ana_dropdown")

    async def callback(self, interaction: discord.Interaction):
        kategori_ismi = self.values[0]
        await interaction.response.send_modal(DestekSorunuModal(kategori=kategori_ismi))

class DestekPanelView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(DestekDropdown())

# === DİĞER RESMİ CLASSLAR ===
class BasvuruIncelemeView(View):
    def __init__(self): super().__init__(timeout=None)

class YetkiliBasvuruModal(Modal, title="MTTS Yetkili Başvuru Formu"):
    ad = TextInput(label="Adınız", placeholder="Örn: Ahmet", required=True)
    gorev = TextInput(label="İstediğiniz Görev", placeholder="Örn: Moderatör", required=True)
    aktiflik = TextInput(label="Haftalık Aktiflik Süreniz", placeholder="Örn: Haftada 20 saat", required=True)
    deneyim = TextInput(label="Daha Önce Yetkili Oldunuz mu?", placeholder="Deneyimleriniz...", style=discord.TextStyle.paragraph, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message("✅ Başvurunuz başarıyla iletildi!", ephemeral=True)

class YetkiliBasvuruView(View):
    def __init__(self): super().__init__(timeout=None)

class RolBasvuruView(View):
    def __init__(self): super().__init__(timeout=None)

# === SLASH KOMUTLARI ===
@bot.tree.command(name="destek-panel", description="MTTS Yenilenmiş Açılır Menülü Destek panelini kurar.")
@app_commands.checks.has_permissions(administrator=True)
async def slash_destek_panel(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📥 Destek Menüsü",
        description=(
            "Aşağıdaki menüden destek talebi açabilirsiniz.\n\n"
            "• **Yetkilileri meşgul etmek yasaktır.**\n"
            "• **Destek taleplerinizi kategorilere göre açın.**\n"
            "• **Uygun kanal seçildikten sonra destek ekibi bilgilendirilecektir.**\n\n"
            f"Bir kategori seçerek destek talebi açabilirsiniz. • {discord.utils.utcnow().strftime('%d.%m.%Y %H:%M')}"
        ),
        color=discord.Color.from_rgb(46, 204, 113)
    )
    if interaction.guild.icon:
        embed.set_thumbnail(url=interaction.guild.icon.url)
    await interaction.channel.send(embed=embed, view=DestekPanelView())
    await interaction.response.send_message("Destek paneli başarıyla kuruldu.", ephemeral=True)

@bot.tree.command(name="sil", description="Belirtilen miktarda mesajı siler.")
@app_commands.checks.has_permissions(administrator=True)
async def slash_sil(interaction: discord.Interaction, miktar: int):
    await interaction.response.defer(ephemeral=True)
    silinen = await interaction.channel.purge(limit=miktar)
    await interaction.followup.send(f"✅ {len(silinen)} adet mesaj silindi.", ephemeral=True)

# === BOT BAŞLAMA VE VIEW KAYITLARI ===
@bot.event
async def on_ready():
    bot.add_view(DestekPanelView())
    bot.add_view(DestekKanalIciView())
    bot.add_view(YetkiliBasvuruView())
    bot.add_view(RolBasvuruView())
    await bot.tree.sync()
    print("--- Giriş Çıkış ve Tüm Sistemler Aktif! ---")

keep_alive()
bot.run(os.environ.get("DISCORD_TOKEN"))
