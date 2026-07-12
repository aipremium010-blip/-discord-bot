import discord
import os
import random
import asyncio
import re
import time
from discord import app_commands
from discord.ui import Select, Modal, TextInput, View
from discord.ext import commands
from threading import Thread
from flask import Flask

# === AYARLAR VE KANAL ID'LERİ ===
BAŞVURU_LOG_KANAL_ID = 1524879141793435689
GIRIS_CIKIS_KANAL_ID = 123456789012345678  # Giriş-Çıkış log kanal ID'si
REKLAM_KANAL_ID = 112233445566778899      # Sunucudaki aktif reklamların yayınlandığı kanal ID'si

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
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# === SÜRE DÖNÜŞTÜRÜCÜ FONKSİYON ===
def parse_duration(duration_str: str) -> int:
    match = re.match(r"(\d+)([smhd]?)", duration_str.lower().strip())
    if not match:
        return 0
    amount = int(match.group(1))
    unit = match.group(2)
    
    if unit == 's':
        return amount
    elif unit == 'm':
        return amount * 60
    elif unit == 'h':
        return amount * 3600
    elif unit == 'd':
        return amount * 86400
    else:
        return amount

# === GİRİŞ VE ÇIKIŞ SİSTEMİ ===
@bot.event
async def on_member_join(member):
    channel = member.guild.get_channel(GIRIS_CIKIS_KANAL_ID)
    if channel:
        embed = discord.Embed(
            description=f"{member.mention} aramıza hoş geldin! **{member.guild.member_count}** kişiyiz.\n\n"
                        f"📢 **Partnerlikler ve Güncel Reklamlar için:** <#{REKLAM_KANAL_ID}> kanalına göz atmayı unutma!",
            color=discord.Color.from_rgb(46, 204, 113)
        )
        embed.set_author(name="📥 Sunucuya Katıldı & Greet Bildirimi!")
        embed.set_thumbnail(url=member.display_avatar.url)
        await channel.send(embed=embed)

@bot.event
async def on_member_remove(member):
    channel = member.guild.get_channel(GIRIS_CIKIS_KANAL_ID)
    if channel:
        embed = discord.Embed(
            description=f"**{member.name}** aramızdan ayrıldı. **{member.guild.member_count}** kişi kaldık.",
            color=discord.Color.from_rgb(231, 76, 60)
        )
        embed.set_author(name="📤 Sunucudan Ayrıldı!")
        embed.set_thumbnail(url=member.display_avatar.url)
        await channel.send(embed=embed)

# === BUTONLU ÇEKİLİŞ SİSTEMİ ALTYAPISI ===
class CekilisButonView(View):
    def __init__(self, odul: str, bitis_timestamp: int, kazanan_sayisi: int):
        super().__init__(timeout=None) # Bot kapanıp açılsa da butonlar çalışmaya devam eder
        self.odul = odul
        self.bitis_timestamp = bitis_timestamp
        self.kazanan_sayisi = kazanan_sayisi
        self.katilimcilar = set() # Aynı kişinin defalarca basmasını engellemek için set kullanıyoruz

    @discord.ui.button(emoji="🎉", style=discord.ButtonStyle.primary, custom_id="cekilis_katil_butonu")
    async def katil_butonu(self, interaction: discord.Interaction, button: discord.Button):
        # Çekiliş süresi bittiyse girişi engelle
        if int(time.time()) >= self.bitis_timestamp:
            await interaction.response.send_message("❌ Bu çekiliş çoktan sona erdi!", ephemeral=True)
            return

        user_id = interaction.user.id
        if user_id in self.katilimcilar:
            self.katilimcilar.remove(user_id)
            await interaction.response.send_message("👋 Çekilişten başarıyla ayrıldınız.", ephemeral=True)
        else:
            self.katilimcilar.add(user_id)
            await interaction.response.send_message("🎉 Çekilişe başarıyla katıldınız! Bol şans.", ephemeral=True)
        
        # Embed üzerindeki katılımcı sayısını anlık olarak güncelle
        embed = interaction.message.embeds[0]
        embed.description = (
            f"Katılmak için aşağıdaki *Butona* tıklayın!\n\n"
            f"•   Süre: <t:{self.bitis_timestamp}:R>\n"
            f"•   Kazanan Sayısı: {self.kazanan_sayisi}\n"
            f"•   Katılımcı Sayısı: {len(self.katilimcilar)}"
        )
        await interaction.message.edit(embed=embed, view=self)

# === 1. DESTEK SİSTEMİ ===
class DestekKanalIciView(View):
    def __init__(self):
        super().__init__(timeout=None)
        
    @discord.ui.button(label="Kapat", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="ticket_kapat_btn_yeni")
    async def ticket_kapat(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.defer()
        await interaction.channel.send("🔒 Bu destek talebi 5 saniye içinde kapatılıyor...")
        await asyncio.sleep(5)
        await interaction.channel.delete()

    @discord.ui.button(label="Aktif Yetkililer", style=discord.ButtonStyle.primary, emoji="👤", custom_id="ticket_aktif_yetkililer")
    async def aktif_yetkililer(self, interaction: discord.Interaction, button: discord.Button):
        online_staff = [m.mention for m in interaction.guild.members if not m.bot and m.guild_permissions.manage_messages and m.status != discord.Status.offline]
        mentions = ", ".join(online_staff[:5]) if online_staff else "Şu an aktif yetkili bulunamadı."
        await interaction.response.send_message(f"🔔 **Aktif Yetkililer Bilgilendirildi:** {mentions}", ephemeral=True)

    @discord.ui.button(label="Yardım Al", style=discord.ButtonStyle.success, emoji="🆘", custom_id="ticket_yardim_al")
    async def yardim_al(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.send_message("🚨 Destek ekibine acil çağrı gönderildi! En kısa sürede odaklanacaklar.", ephemeral=False)

class DestekSorunuModal(Modal):
    def __init__(self, kategori: str):
        super().__init__(title=f"{kategori.capitalize()} Destek Formu")
        self.kategori = kategori
        self.sorun = TextInput(label="Kısaca Sorununuzu Bildirin", placeholder="Lütfen talebinizin nedenini yazın...", style=discord.TextStyle.paragraph, required=True)
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
        embed.add_field(name="📌 Konu", value=self.sorun.value, inline=False)
        embed.add_field(name="📁 Kategori", value=self.kategori, inline=True)
        embed.add_field(name="👤 Kullanıcı", value=f"{member.name}", inline=True)
        embed.add_field(name="🆔 Kullanıcı ID", value=f"{member.id}", inline=True)
        
        await ticket_channel.send(content=f"{member.mention}, destek talebiniz açıldı.", embed=embed, view=DestekKanalIciView())
        await interaction.followup.send(f"✅ Destek talebiniz açıldı: {ticket_channel.mention}", ephemeral=True)

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
        await interaction.response.send_modal(DestekSorunuModal(kategori=self.values[0]))

class DestekPanelView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(DestekDropdown())

# === 2. GÜNCEL REKLAM VE PİNG SİSTEMLERİ ===
class ReklamHizmetModal(Modal):
    def __init__(self, hizmet_turu: str, detaylar: str = ""):
        super().__init__(title=f"{hizmet_turu} Başvuru Formu")
        self.hizmet_turu = hizmet_turu

        self.ad = TextInput(label="İsminiz", placeholder="Lütfen adınızı girin...", required=True)
        self.paket_secimi = TextInput(label="Seçtiğiniz Paket / Ping Türü", default=detaylar, placeholder="Örn: Demir Paket / Everyone Ping vb.", required=True)
        self.Detay = TextInput(label="Sunucu / Hizmet Detayı", placeholder="Reklamı yapılacak içerik veya detaylar...", style=discord.TextStyle.paragraph, required=True)
        self.link = TextInput(label="Yönlendirilecek Link", placeholder="discord.gg/...", required=True)

        self.add_item(self.ad)
        self.add_item(self.paket_secimi)
        self.add_item(self.Detay)
        self.add_item(self.link)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        log_kanali = interaction.guild.get_channel(BAŞVURU_LOG_KANAL_ID)
        
        if log_kanali:
            greet_durumu = "✅ Mevcut (+ Greet Karşılama)" if "Altın" in self.paket_secimi.value or "Elmas" in self.paket_secimi.value or "Netherite" in self.paket_secimi.value else "❌ Yok"
            
            embed = discord.Embed(title="📢 Yeni Reklam / Hizmet Başvurusu!", color=discord.Color.green())
            embed.add_field(name="Kullanıcı", value=interaction.user.mention, inline=True)
            embed.add_field(name="Hizmet Grubu", value=self.hizmet_turu, inline=True)
            embed.add_field(name="Başvuran İsmi", value=self.ad.value, inline=True)
            embed.add_field(name="Seçtiği Paket/Ping", value=self.paket_secimi.value, inline=True)
            embed.add_field(name="Greet Özelliği", value=greet_durumu, inline=True)
            embed.add_field(name="Link", value=self.link.value, inline=False)
            embed.add_field(name="Açıklama / Detay", value=self.Detay.value, inline=False)
            embed.set_footer(text="Gerekli ödeme/şart kontrollerini yapıp el ile işleme alın.")
            
            view = View()
            class GreetMetniButon(discord.ui.Button):
                def __init__(self, link, aciklama):
                    super().__init__(label="Greet Yazısını Al", style=discord.ButtonStyle.secondary, emoji="📋")
                    self.link = link
                    self.aciklama = aciklama
                async def callback(self, inter: discord.Interaction):
                    greet_text = f"**🌟 YENİ BİR PARTNER / REKLAM!**\n\n📌 **Açıklama:** {self.aciklama}\n🔗 **Katılmak İçin:** {self.link}\n\n*Sunucumuza destekleri için teşekkür ederiz! @everyone*"
                    await inter.response.send_message(f"```\n{greet_text}\n
