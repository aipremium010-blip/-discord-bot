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
from datetime import datetime

# === AYARLAR VE KANAL ID'LERİ ===
BAŞVURU_LOG_KANAL_ID = 1524879141793435689
GIRIS_CIKIS_KANAL_ID = 123456789012345678  # Giriş-Çıkış log kanal ID'si
REKLAM_KANAL_ID = 112233445566778899      # Reklamların gideceği kanal ID'si
YETKILI_ROL_ID = 987654321098765432        # Başvuru onaylanınca verilecek Yetkili Rol ID'si
ILAN_VER_ROL_ID = 1524866585637031958      # !ilan-ver komutunu kullanabilecek Özel Rol ID'si
ILAN_KANAL_ID = 1524866586912227330       # !ilan-ver komutunun çalışacağı TEK KANAL ID'si

# === RENDER KEEPALIVE SİSTEMİ ===
app = Flask('')

@app.route('/')
def home():
    return "MTTS Bot Aktif!"

def run_web():
    # Render'ın dinamik port atamasını yakalar, yoksa varsayılan 8080'de açar.
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

# === BOT HAZIR OLDUĞUNDA ===
@bot.event
async def on_ready():
    print(f"🤖 {bot.user.name} olarak giriş yapıldı!")
    try:
        synced = await bot.tree.sync()
        print(f"✨ {len(synced)} adet slash komutu başarıyla senkronize edildi.")
    except Exception as e:
        print(f"❌ Komutlar senkronize edilirken hata oluştu: {e}")

# === SÜRE DÖNÜŞTÜRÜCÜ FONKSİYON ===
def parse_duration(duration_str: str) -> int:
    match = re.match(r"(\d+)([smhd]?)", duration_str.lower().strip())
    if not match:
        return 0
    amount = int(match.group(1))
    unit = match.group(2)
    
    if unit == 's': return amount
    elif unit == 'm': return amount * 60
    elif unit == 'h': return amount * 3600
    elif unit == 'd': return amount * 86400
    else: return amount

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
        embed.set_author(name="📥 Sunucuya Katıldı!")
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

# === ORTAK BAŞVURU INCELEME BUTONLARI ===
class GenelBasvuruIncelemeView(View):
    def __init__(self, tur: str):
        super().__init__(timeout=None)
        self.tur = tur

    @discord.ui.button(label="Onayla", style=discord.ButtonStyle.success, custom_id="genel_onay_btn")
    async def onay(self, interaction: discord.Interaction, button: discord.Button):
        if not interaction.user.guild_permissions.administrator and not interaction.guild.get_role(YETKILI_ROL_ID) in interaction.user.roles:
            await interaction.response.send_message("❌ Bu başvuruyu incelemek için gerekli yetkiniz bulunmamaktadır!", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        embed = interaction.message.embeds[0]
        
        kullanici_mentions = embed.fields[0].value
        kullanici_id = int(re.search(r'\d+', kullanici_mentions).group())
        uye = interaction.guild.get_member(kullanici_id)

        embed.color = discord.Color.green()
        embed.title = f"✅ {self.tur} Başvurusu Kabul Edildi!"
        
        self.clear_items()
        await interaction.message.edit(embed=embed, view=self)
        await interaction.followup.send(f"✅ Başvuru başarıyla onaylandı.", ephemeral=True)
        
        if uye:
            try:
                await uye.send(f"🎉 **Tebrikler!** Sunucumuzda yapmış olduğunuz **{self.tur}** talebiniz yetkililerce onaylandı!")
            except: pass

    @discord.ui.button(label="Reddet", style=discord.ButtonStyle.danger, custom_id="genel_red_btn")
    async def reddet(self, interaction: discord.Interaction, button: discord.Button):
        if not interaction.user.guild_permissions.administrator and not interaction.guild.get_role(YETKILI_ROL_ID) in interaction.user.roles:
            await interaction.response.send_message("❌ Bu başvuruyu incelemek için gerekli yetkiniz bulunmamaktadır!", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        embed = interaction.message.embeds[0]
        
        kullanici_mentions = embed.fields[0].value
        kullanici_id = int(re.search(r'\d+', kullanici_mentions).group())
        uye = interaction.guild.get_member(kullanici_id)

        embed.color = discord.Color.red()
        embed.title = f"❌ {self.tur} Başvurusu Reddedildi"
        
        self.clear_items()
        await interaction.message.edit(embed=embed, view=self)
        await interaction.followup.send("❌ Başvuru reddedildi.", ephemeral=True)
        
        if uye:
            try:
                await uye.send(f"Maalesef, sunucumuzda yapmış olduğunuz **{self.tur}** talebiniz yetkililer tarafından uygun görülmemiştir.")
            except: pass

# === BUTONLU ÇEKİLİŞ SİSTEMİ ALTYAPISI ===
class CekilisButonView(View):
    def __init__(self, odul: str, bitis_timestamp: int, kazanan_sayisi: int):
        super().__init__(timeout=None)
        self.odul = odul
        self.bitis_timestamp = bitis_timestamp
        self.kazanan_sayisi = kazanan_sayisi
        self.katilimcilar = set()

    @discord.ui.button(emoji="🎉", style=discord.ButtonStyle.primary, custom_id="cekilis_katil_butonu")
    async def katil_butonu(self, interaction: discord.Interaction, button: discord.Button):
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
        online_staff = [m.mention for m in interaction.guild.members if not m.bot and (m.guild_permissions.manage_messages or interaction.guild.get_role(ILAN_VER_ROL_ID) in m.roles) and m.status != discord.Status.offline]
        text_mentions = ", ".join(online_staff[:5]) if online_staff else "Şu an aktif yetkili bulunamadı."
        await interaction.response.send_message(f"🔔 **Aktif Ekip Bilgilendirildi:** {text_mentions}", ephemeral=True)

    @discord.ui.button(label="Yardım Al", style=discord.ButtonStyle.success, emoji="🆘", custom_id="ticket_yardim_al")
    async def yardim_al(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.send_message("🚨 Destek ekibine acil çağrı gönderildi!", ephemeral=False)

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
            if role.permissions.administrator or role.id == YETKILI_ROL_ID:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        kanal_adi = f"{self.kategori}-{member.name}".lower()
        ticket_channel = await guild.create_text_channel(name=kanal_adi, overwrites=overwrites)
        
        embed = discord.Embed(title="📋 Destek Talebi", color=discord.Color.from_rgb(46, 204, 113))
        embed.add_field(name="📌 Konu", value=self.sorun.value, inline=False)
        embed.add_field(name="📁 Kategori", value=self.kategori, inline=True)
        embed.add_field(name="👤 Kullanıcı", value=f"{member.name}", inline=True)
        embed.add_field(name="🆔 Kullanıcı ID", value=f"{member.id}", inline=True)
        
        await ticket_channel.send(content=f"{member.mention}, destek talebiniz açıldı. Yetkililerimiz sizinle en kısa sürede ilgilenecektir.", embed=embed, view=DestekKanalIciView())
        await interaction.followup.send(f"✅ Destek talebiniz açıldı: {ticket_channel.mention}", ephemeral=True)

class DestekDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Partnerlik", value="partnerlik", emoji="📄"),
            discord.SelectOption(label="Şikayet", value="sikayet", emoji="🚨"),
            discord.SelectOption(label="Yetkili Başvurusu", value="yetkili", emoji="📁"),
            discord.SelectOption(label="Reklam / İlan İşlemleri", value="reklam_ilan", emoji="💵"),
            discord.SelectOption(label="Genel", value="genel", emoji="📜")
        ]
        super().__init__(placeholder="📌 Bir destek kategorisi seçin", min_values=1, max_values=1, options=options, custom_id="destek_ana_dropdown")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(DestekSorunuModal(kategori=self.values[0]))

class DestekPanelView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(DestekDropdown())

# === 2. REKLAM VE PİNG SİSTEMLERİ ===
class ReklamHizmetModal(Modal):
    def __init__(self, hizmet_turu: str, detaylar: str = ""):
        super().__init__(title=f"{hizmet_turu} Başvuru Formu")
        self.hizmet_turu = hizmet_turu

        self.ad = TextInput(label="İsminiz", placeholder="Lütfen adınızı girin...", required=True)
        self.paket_secimi = TextInput(label="Seçtiğiniz Paket / Ping Türü", default=detaylar, placeholder="Örn: Demir Paket vb.", required=True)
        self.Detay = TextInput(label="Sunucu / Hizmet Detayı", placeholder="Detaylar...", style=discord.TextStyle.paragraph, required=True)
        self.link = TextInput(label="Yönlendirilecek Link", placeholder="discord.gg/...", required=True)

        self.add_item(self.ad)
        self.add_item(self.paket_secimi)
        self.add_item(self.Detay)
        self.add_item(self.link)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        log_kanali = interaction.guild.get_channel(BAŞVURU_LOG_KANAL_ID)
        
        if log_kanali:
            embed = discord.Embed(title="📢 Yeni Reklam / Hizmet Başvurusu!", color=discord.Color.blue())
            embed.add_field(name="Kullanıcı", value=interaction.user.mention, inline=True)
            embed.add_field(name="Hizmet Grubu", value=self.hizmet_turu, inline=True)
            embed.add_field(name="Başvuran İsmi", value=self.ad.value, inline=True)
            embed.add_field(name="Seçtiği Paket/Ping", value=self.paket_secimi.value, inline=True)
            embed.add_field(name="Link", value=self.link.value, inline=False)
            embed.add_field(name="Açıklama / Detay", value=self.Detay.value, inline=False)
            
            await log_kanali.send(embed=embed, view=GenelBasvuruIncelemeView(tur="Reklam"))
            
        await interaction.followup.send("✅ Reklam başvurunuz başarıyla yetkililere iletildi!", ephemeral=True)

class ReklamPaketleriSubDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Demir Paket - 100 TL", value="demir", emoji="🪙"),
            discord.SelectOption(label="Altın Paket - 150 TL", value="altin", emoji="🥇"),
            discord.SelectOption(label="Elmas Paket - 300 TL", value="elmas", emoji="💎"),
            discord.SelectOption(label="Netherite Paket - 400 TL", value="netherite", emoji="🔥")
        ]
        super().__init__(placeholder="İncelemek istediğiniz reklam paketini seçin", options=options, custom_id="mtts_paket_alt_dropdown")

    async def callback(self, interaction: discord.Interaction):
        secilen = self.values[0]
        embed = discord.Embed(color=discord.Color.from_rgb(41, 128, 185))
        
        if secilen == "demir":
            embed.title = "🪙 Demir Reklam Paketi - 100 TL"
            embed.description = "• **Süre:** 3 Gün\n• **Etiket:** 1 @everyone\n• **Çekiliş:** Onlardan"
        elif secilen == "altin":
            embed.title = "🥇 Altın Reklam Paketi - 150 TL"
            embed.description = "• **Süre:** 5 Gün\n• **Etiket:** 1 @everyone\n• **Çekiliş:** Bizden"
        elif secilen == "elmas":
            embed.title = "💎 Elmas Reklam Paketi - 300 TL"
            embed.description = "• **Süre:** 7 Gün\n• **Etiket:** 1 @everyone + 1 @here"
        elif secilen == "netherite":
            embed.title = "🔥 Netherite Reklam Paketi - 400 TL"
            embed.description = "• **Süre:** 14 Gün\n• **Etiket:** 2 @everyone"

        view = View()
        class BasvurButton(discord.ui.Button):
            def __init__(self, paket_adi):
                super().__init__(label=f"{paket_adi} Satın Al", style=discord.ButtonStyle.success, emoji="💳")
                self.paket_adi = paket_adi
            async def callback(self, inter: discord.Interaction):
                await inter.response.send_modal(ReklamHizmetModal(hizmet_turu="MTTS Reklam Paketleri", detaylar=self.paket_adi))
                
        view.add_item(BasvurButton(paket_adi=f"{secilen.capitalize()} Paket"))
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class HizmetlerDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Ping Hizmetleri", value="Ping Hizmetleri", emoji="📢"),
            discord.SelectOption(label="MTTS Reklam Paketleri", value="MTTS Reklam Paketleri", emoji="💵")
        ]
        super().__init__(placeholder="Aşağıdaki menüden paketleri inceleyebilirsiniz.", options=options, custom_id="mtts_hizmetler_dropdown")

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "MTTS Reklam Paketleri":
            sub_view = View()
            sub_view.add_item(ReklamPaketleriSubDropdown())
            await interaction.response.send_message("🔎 Detaylarını görmek istediğiniz paketi seçin:", view=sub_view, ephemeral=True)
        else:
            await interaction.response.send_modal(ReklamHizmetModal(hizmet_turu=self.values[0]))

class HizmetlerPanelView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(HizmetlerDropdown())

# === 3. YETKİLİ / ROL BAŞVURU SİSTEMLERİ ===
class YetkiliBasvuruIncelemeView(View):
    def __init__(self, basvuran_id: int = None):
        super().__init__(timeout=None)
        self.basvuran_id = basvuran_id

    @discord.ui.button(label="Onayla", style=discord.ButtonStyle.success, custom_id="yb_onay_butonu")
    async def onay(self, interaction: discord.Interaction, button: discord.Button):
        if not interaction.user.guild_permissions.administrator and not interaction.guild.get_role(YETKILI_ROL_ID) in interaction.user.roles:
            await interaction.response.send_message("❌ Bu başvuruyu incelemek için gerekli yetkiniz bulunmamaktadır!", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        embed = interaction.message.embeds[0]
        kullanici_mentions = embed.fields[0].value
        kullanici_id = int(re.search(r'\d+', kullanici_mentions).group())
        
        uye = interaction.guild.get_member(kullanici_id)
        rol = interaction.guild.get_role(YETKILI_ROL_ID)
        
        if uye and rol:
            await uye.add_roles(rol)
            self.clear_items()
            embed.color = discord.Color.green()
            embed.title = "✅ Yetkili Başvurusu Kabul Edildi!"
            await interaction.message.edit(embed=embed, view=self)
            await interaction.followup.send(f"✅ {uye.mention} onaylandı ve rolü verildi.", ephemeral=True)
            try: await uye.send("🎉 Yetkili başvurunuz kabul edildi!")
            except: pass
        else:
            await interaction.followup.send("❌ Hata oluştu!", ephemeral=True)

    @discord.ui.button(label="Reddet", style=discord.ButtonStyle.danger, custom_id="yb_red_butonu")
    async def reddet(self, interaction: discord.Interaction, button: discord.Button):
        if not interaction.user.guild_permissions.administrator and not interaction.guild.get_role(YETKILI_ROL_ID) in interaction.user.roles:
            await interaction.response.send_message("❌ Bu başvuruyu incelemek için gerekli yetkiniz bulunmamaktadır!", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        embed = interaction.message.embeds[0]
        kullanici_mentions = embed.fields[0].value
        kullanici_id = int(re.search(r'\d+', kullanici_mentions).group())
        uye = interaction.guild.get_member(kullanici_id)
        
        self.clear_items()
        embed.color = discord.Color.red()
        embed.title = "❌ Yetkili Başvurusu Reddedildi"
        await interaction.message.edit(embed=embed, view=self)
        await interaction.followup.send("❌ Başvuru reddedildi.", ephemeral=True)
        if uye:
            try: await uye.send("Maalesef, yetkili başvurunuz olumsuz sonuçlanmıştır.")
            except: pass

class YetkiliBasvuruModal(Modal, title="MTTS Yetkili Başvuru Formu"):
    ad = TextInput(label="Adınız", required=True)
    gorev = TextInput(label="İstediğiniz Görev", required=True)
    aktiflik = TextInput(label="Haftalık Aktiflik Süreniz", required=True)
    deneyim = TextInput(label="Deneyimleriniz", style=discord.TextStyle.paragraph, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        log_kanali = interaction.guild.get_channel(BAŞVURU_LOG_KANAL_ID)
        if log_kanali:
            embed = discord.Embed(title="Yeni Yetkili Başvurusu Geldi!", color=discord.Color.gold())
            embed.add_field(name="Başvuran", value=interaction.user.mention, inline=True)
            embed.add_field(name="İsim", value=self.ad.value, inline=True)
            embed.add_field(name="Görev", value=self.gorev.value, inline=True)
            embed.add_field(name="Aktiflik", value=self.aktiflik.value, inline=True)
            embed.add_field(name="Deneyim", value=self.deneyim.value, inline=False)
            await log_kanali.send(embed=embed, view=YetkiliBasvuruIncelemeView(interaction.user.id))
        await interaction.response.send_message("✅ Başvurunuz yetkililere iletildi!", ephemeral=True)

class YetkiliBasvuruView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Başvuru Formunu Aç", style=discord.ButtonStyle.primary, custom_id="yb_form_ac")
    async def basvuru_ac(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.send_modal(YetkiliBasvuruModal())

class RolTalepModal(Modal):
    def __init__(self, rol_label: str):
        super().__init__(title=f"{rol_label} Rol Başvuru Formu")
        self.rol_label = rol_label
        self.ad = TextInput(label="İsminiz", required=True)
        self.sunucu_adi = TextInput(label="Sunucu İsminiz", required=True)
        self.sunucu_det= TextInput(label="Sunucu Detay", style=discord.TextStyle.paragraph, required=True)
        self.sunucu_link = TextInput(label="Sunucu Link", placeholder="discord.gg/...", required=True)
        self.add_item(self.ad)
        self.add_item(self.sunucu_adi)
        self.add_item(self.sunucu_det)
        self.add_item(self.sunucu_link)

    async def on_submit(self, interaction: discord.Interaction):
        log_kanali = interaction.guild.get_channel(BAŞVURU_LOG_KANAL_ID)
        if log_kanali:
            embed = discord.Embed(title="Yeni Özel Rol Talebi!", color=discord.Color.purple())
            embed.add_field(name="Kullanıcı", value=interaction.user.mention, inline=True)
            embed.add_field(name="İstenen Rol", value=self.rol_label, inline=True)
            embed.add_field(name="İsim", value=self.ad.value, inline=True)
            embed.add_field(name="Sunucu", value=self.sunucu_adi.value, inline=True)
            embed.add_field(name="Link", value=self.sunucu_link.value, inline=False)
            embed.add_field(name="Detay", value=self.sunucu_det.value, inline=False)
            await log_kanali.send(embed=embed, view=GenelBasvuruIncelemeView(tur="Özel Rol"))
        await interaction.response.send_message("✅ Rol talebiniz alındı.", ephemeral=True)

class RolDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Sunucu Sahibi", value="sunucu", emoji="👑"),
            discord.SelectOption(label="Klan Sahibi", value="klan", emoji="⚔️"),
            discord.SelectOption(label="Hosting Sahibi", value="hosting", emoji="🖥️"),
            discord.SelectOption(label="Takım Sahibi", value="takim", emoji="🛡️"),
            discord.SelectOption(label="İçerik Üreticisi", value="icerik", emoji="🎥")  # İçerik Üreticisi eklendi
        ]
        super().__init__(placeholder="Talep etmek istediğiniz rolü seçin", options=options, custom_id="rol_talep_dropdown")

    async def callback(self, interaction: discord.Interaction):
        rol_isimleri = {
            "sunucu": "Sunucu Sahibi", 
            "klan": "Klan Sahibi", 
            "hosting": "Hosting Sahibi", 
            "takim": "Takım Sahibi",
            "icerik": "İçerik Üreticisi"  # Map listesine eklendi
        }
        await interaction.response.send_modal(RolTalepModal(rol_label=rol_isimleri[self.values[0]]))

class RolBasvuruView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(RolDropdown())

# === 4. SLASH KOMUTLARI ===

@bot.tree.command(name="paketler", description="Reklam paketlerinin listesini gösterir.")
async def slash_paketler(interaction: discord.Interaction):
    sub_view = View()
    sub_view.add_item(ReklamPaketleriSubDropdown())
    await interaction.response.send_message("🔎 Reklam Paketini seçin:", view=sub_view, ephemeral=True)

@bot.tree.command(name="reklam-hizmet-panel", description="Hizmet paneli kurar.")
@app_commands.checks.has_permissions(administrator=True)
async def slash_reklam_hizmet_panel(interaction: discord.Interaction):
    embed = discord.Embed(title="🤖 MTTS Hizmetleri", description="Aşağıdaki menüden paketleri inceleyebilirsiniz.", color=discord.Color.blue())
    await interaction.channel.send(embed=embed, view=HizmetlerPanelView())
    await interaction.response.send_message("Panel kuruldu.", ephemeral=True)

@bot.tree.command(name="anket", description="Oylama başlatır.")
@app_commands.checks.has_permissions(manage_messages=True)
async def slash_anket(interaction: discord.Interaction, soru: str):
    embed = discord.Embed(title="📊 Yeni Anket / Oylama", description=soru, color=discord.Color.purple())
    embed.set_footer(text=f"Başlatan: {interaction.user.name}")
    await interaction.response.send_message("Anket oluşturuluyor...", ephemeral=True)
    msg = await interaction.channel.send(embed=embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")

@bot.tree.command(name="cekilis", description="Butonlu çekiliş düzenler.")
@app_commands.checks.has_permissions(manage_messages=True)
async def slash_cekilis(interaction: discord.Interaction, sure: str, odul: str, kazanan_sayisi: int = 1):
    saniye = parse_duration(sure)
    if saniye <= 0:
        await interaction.response.send_message("❌ Geçersiz süre formatı!", ephemeral=True)
        return

    bitis_timestamp = int(time.time()) + saniye
    embed = discord.Embed(
        title=f"🎁 {odul} Çekilişi - Başladı!",
        description=f"Katılmak için aşağıdaki *Butona* tıklayın!\n\n•   Süre: <t:{bitis_timestamp}:R>\n•   Kazanan Sayısı: {kazanan_sayisi}\n•   Katılımcı Sayısı: 0",
        color=discord.Color.from_rgb(46, 204, 113)
    )
    await interaction.response.send_message("Çekiliş paneli kuruluyor...", ephemeral=True)
    cekilis_view = CekilisButonView(odul=odul, bitis_timestamp=bitis_timestamp, kazanan_sayisi=kazanan_sayisi)
    msg = await interaction.channel.send(embed=embed, view=cekilis_view)
    
    await asyncio.sleep(saniye)
    
    for item in cekilis_view.children: item.disabled = True
    katilanlar_listesi = list(cekilis_view.katilimcilar)
    
    if katilanlar_listesi:
        gercek_kazanan_sayisi = min(kazanan_sayisi, len(katilanlar_listesi))
        kazananlar = random.sample(katilanlar_listesi, k=gercek_kazanan_sayisi)
        kazanan_mentionlar = ", ".join([f"<@{k_id}>" for k_id in kazananlar])
        
        bitis_embed = discord.Embed(title=f"🎉 {odul} Çekilişi - Sona Erdi!", description=f"•   Kazananlar: {kazanan_mentionlar}\n•   Toplam Katılımcı: {len(katilanlar_listesi)}", color=discord.Color.red())
        await msg.edit(bitis_embed, view=cekilis_view)
        await interaction.channel.send(f"🎉 Tebrikler {kazanan_mentionlar}! **{odul}** çekilişini kazandınız!")
    else:
        iptal_embed = discord.Embed(title=f"❌ {odul} Çekilişi İptal Edildi", description="Katılım olmadı.", color=discord.Color.purple())
        await msg.edit(embed=iptal_embed, view=cekilis_view)

@bot.tree.command(name="destek-panel", description="Görseldeki formatta kurallı lüks Destek panelini kurar.")
@app_commands.checks.has_permissions(administrator=True)
async def slash_destek_panel(interaction: discord.Interaction):
    su_an = datetime.now().strftime("%d.%m.%Y %H:%M")
    
    embed = discord.Embed(
        title="📥 Destek Menüsü",
        description=(
            "Aşağıdaki menüden destek talebi açabilirsiniz.\n\n"
            "**- Yetkilileri meşgul etmek yasaktır.**\n"
            "**- Destek taleplerinizi kategorilere göre açın.**\n"
            "**- Uygun kanal seçildikten sonra destek ekibi bilgilendirilecektir.**\n\n"
            f"Bir kategori seçerek destek talebi açabilirsiniz. - {su_an}"
        ),
        color=discord.Color.from_rgb(46, 204, 113)
    )
    
    if interaction.guild.icon:
        embed.set_thumbnail(url=interaction.guild.icon.url)
        
    await interaction.channel.send(embed=embed, view=DestekPanelView())
    await interaction.response.send_message("Kurallı destek paneli başarıyla kuruldu.", ephemeral=True)

@bot.tree.command(name="yetkili-basvuru-panel", description="Yetkili başvuru panelini kurar.")
@app_commands.checks.has_permissions(administrator=True)
async def slash_yb_panel(interaction: discord.Interaction):
    embed = discord.Embed(title="📋 Yetkili Başvuru Paneli", description="Aşağıdaki butona tıklayarak formu doldurunuz.", color=discord.Color.gold())
    await interaction.channel.send(embed=embed, view=YetkiliBasvuruView())
    await interaction.response.send_message("Panel kuruldu.", ephemeral=True)

@bot.tree.command(name="rol-basvuru-panel", description="Özel rol başvuru panelini kurar.")
@app_commands.checks.has_permissions(administrator=True)
async def slash_rol_panel(interaction: discord.Interaction):
    embed = discord.Embed(title="👑 Özel Rol Başvuru Paneli", description="Aşağıdaki menüden seçim yapın.", color=discord.Color.blue())
    await interaction.channel.send(embed=embed, view=RolBasvuruView())
    await interaction.response.send_message("Panel kuruldu.", ephemeral=True)

@bot.tree.command(name="lock", description="Kanalı kilitle.")
@app_commands.checks.has_permissions(manage_channels=True)
async def slash_lock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message(embed=discord.Embed(description="🔒 Bu kanal kapatılmıştır.", color=discord.Color.red()))

@bot.tree.command(name="unlock", description="Kanal kilidini aç.")
@app_commands.checks.has_permissions(manage_channels=True)
async def slash_unlock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
    await interaction.response.send_message(embed=discord.Embed(description="🔓 Bu kanal açılmıştır.", color=discord.Color.green()))

@bot.tree.command(name="sil", description="Mesaj siler.")
@app_commands.checks.has_permissions(administrator=True)
async def slash_sil(interaction: discord.Interaction, miktar: int):
    await interaction.response.defer(ephemeral=True)
    silinen = await interaction.channel.purge(limit=miktar)
    await interaction.followup.send(f"✅ {len(silinen)} adet mesaj silindi.", ephemeral=True)

# === ANA ÇALIŞTIRMA BLOĞU ===
if __name__ == "__main__":
    # 1. Render için Flask sunucusunu arka planda ayağa kaldırıyoruz
    keep_alive()
    
    # 2. Render Environment Variables panelinden DISCORD_TOKEN'ı çekiyoruz
    token = os.environ.get("DISCORD_TOKEN")
    
    if token:
        try:
            bot.run(token)
        except Exception as e:
            print(f"❌ Bot başlatılırken ölümcül hata: {e}")
    else:
        print("❌ HATA: DISCORD_TOKEN bulunamadı! Lütfen Render panelinden Environment Variables kısmına tokeninizi ekleyin.")
