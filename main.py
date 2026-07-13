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
REKLAM_KANAL_ID = 112233445566778899      # /greet komutunun ve reklamların gideceği kanal ID'si
YETKILI_ROL_ID = 987654321098765432        # Başvuru onaylanınca verilecek Yetkili Rol ID'si

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
class GreetMetniButonView(View):
    def __init__(self):
        super().__init__(timeout=None)
        
    @discord.ui.button(label="Greet Yazısını Al", style=discord.ButtonStyle.secondary, emoji="📋", custom_id="greet_yazisi_butonu")
    async def greet_yazisi_al(self, interaction: discord.Interaction, button: discord.Button):
        embed = interaction.message.embeds[0]
        link_val = "Kanal Bulunamadı"
        desc_val = "Açıklama Bulunamadı"
        
        for field in embed.fields:
            if field.name == "Link":
                link_val = field.value
            elif field.name == "Açıklama / Detay":
                desc_val = field.value

        greet_text = f"**🌟 YENİ BİR PARTNER / REKLAM!**\n\n📌 **Açıklama:** {desc_val}\n🔗 **Katılmak İçin:** {link_val}\n\n*Sunucumuza destekleri için teşekkür ederiz! @everyone*"
        # Syntax hatasını önlemek için tek satırda temiz çıktı verecek şekilde güncellendi:
        await interaction.response.send_message(content=f"```\n{greet_text}\n```\nYukarıdaki kodu kopyalayıp Greet veya Reklam odasına atabilirsiniz.", ephemeral=True)

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
            greet_durumu = "✅ Mevcut (+ Greet Karşılama)" if any(p in self.paket_secimi.value for p in ["Altın", "Elmas", "Netherite"]) else "❌ Yok"
            
            embed = discord.Embed(title="📢 Yeni Reklam / Hizmet Başvurusu!", color=discord.Color.green())
            embed.add_field(name="Kullanıcı", value=interaction.user.mention, inline=True)
            embed.add_field(name="Hizmet Grubu", value=self.hizmet_turu, inline=True)
            embed.add_field(name="Başvuran İsmi", value=self.ad.value, inline=True)
            embed.add_field(name="Seçtiği Paket/Ping", value=self.paket_secimi.value, inline=True)
            embed.add_field(name="Greet Özelliği", value=greet_durumu, inline=True)
            embed.add_field(name="Link", value=self.link.value, inline=False)
            embed.add_field(name="Açıklama / Detay", value=self.Detay.value, inline=False)
            embed.set_footer(text="Gerekli ödeme/şart kontrollerini yapıp el ile işleme alın.")
            
            await log_kanali.send(embed=embed, view=GreetMetniButonView())
            
        await interaction.followup.send("✅ Reklam başvurunuz başarıyla yetkililere iletildi!", ephemeral=True)

class ReklamPaketleriSubDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Demir Paket - 100 TL", value="demir", emoji="🪙", description="3 Gün | 1 Everyone | Çekiliş Onlardan"),
            discord.SelectOption(label="Altın Paket - 150 TL", value="altin", emoji="🥇", description="5 Gün | 1 Everyone | Çekiliş Bizden + Greet"),
            discord.SelectOption(label="Elmas Paket - 300 TL", value="elmas", emoji="💎", description="7 Gün | 1 Everyone + 1 Here | Çekiliş Bizden + Greet"),
            discord.SelectOption(label="Netherite Paket - 400 TL", value="netherite", emoji="🔥", description="14 Gün | 2 Everyone | Özel Oda + Greet")
        ]
        super().__init__(placeholder="İncelemek istediğiniz reklam paketini seçin", options=options, custom_id="mtts_paket_alt_dropdown")

    async def callback(self, interaction: discord.Interaction):
        secilen = self.values[0]
        embed = discord.Embed(color=discord.Color.from_rgb(41, 128, 185))
        
        if secilen == "demir":
            embed.title = "🪙 Demir Reklam Paketi - 100 TL"
            embed.description = "• **Süre:** 3 Gün Sabit\n• **Etiket:** 1 Adet @everyone\n• **Özellikler:** Özel Oda, Reklam Texti\n• **Greet Desteği:** ❌ Yok\n• **Çekiliş:** Çekiliş onlardan (Ödülü kendileri karşılar)"
        elif secilen == "altin":
            embed.title = "🥇 Altın Reklam Paketi - 150 TL"
            embed.description = "• **Süre:** 5 Gün Sabit\n• **Etiket:** 1 Adet @everyone\n• **Özellikler:** Özel Oda, Reklam Texti, Greet (Karşılama Odasında Görünme)\n• **Greet Desteği:** Aktif\n• **Çekiliş:** Çekiliş bizden (Siz karşılarsınız)"
        elif secilen == "elmas":
            embed.title = "💎 Elmas Reklam Paketi - 300 TL"
            embed.description = "• **Süre:** 7 Gün Sabit\n• **Etiket:** 1 Adet @everyone + 1 Adet @here\n• **Özellikler:** Özel Oda, Greet Karşılama Desteği\n• **Greet Desteği:** Aktif\n• **Çekiliş:** Çekiliş bizden (Siz karşılarsınız)"
        elif secilen == "netherite":
            embed.title = "🔥 Netherite Reklam Paketi - 400 TL"
            embed.description = "• **Süre:** 14 Gün Sabit\n• **Etiket:** 2 Adet @everyone\n• **Özellikler:** Özel Oda, Reklam Texti, Greet Karşılama Desteği\n• **Greet Desteği:** Aktif"

        view = View()
        class BasvurButton(discord.ui.Button):
            def __init__(self, paket_adi):
                super().__init__(label=f"{paket_adi} Satın Al / Başvur", style=discord.ButtonStyle.success, emoji="💳")
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
            await interaction.response.send_message("🔎 Detaylarını görmek istediğiniz maden paketini seçin:", view=sub_view, ephemeral=True)
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
        await interaction.response.defer(ephemeral=True)
        
        embed = interaction.message.embeds[0]
        kullanici_mentions = embed.fields[0].value
        kullanici_id = int(re.search(r'\d+', kullanici_mentions).group())
        
        uye = interaction.guild.get_member(kullanici_id)
        rol = interaction.guild.get_role(YETKILI_ROL_ID)
        
        if uye and rol:
            await uye.add_roles(rol)
            button.disabled = True
            for child in self.children:
                if child.custom_id == "yb_red_butonu":
                    self.remove_item(child)
            
            embed.color = discord.Color.green()
            embed.title = "✅ Yetkili Başvurusu Kabul Edildi!"
            await interaction.message.edit(embed=embed, view=self)
            await interaction.followup.send(f"✅ {uye.mention} başarıyla yetkili olarak onaylandı ve rolü verildi.", ephemeral=True)
            try:
                await uye.send("🎉 **Tebrikler!** MTTS Yetkili başvurunuz yetkililer tarafından kabul edildi ve yetkileriniz tanımlandı!")
            except:
                pass
        else:
            await interaction.followup.send("❌ Kullanıcı sunucuda bulunamadı veya Belirtilen Rol ID hatalı!", ephemeral=True)

    @discord.ui.button(label="Reddet", style=discord.ButtonStyle.danger, custom_id="yb_red_butonu")
    async def reddet(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.defer(ephemeral=True)
        
        embed = interaction.message.embeds[0]
        kullanici_mentions = embed.fields[0].value
        kullanici_id = int(re.search(r'\d+', kullanici_mentions).group())
        
        uye = interaction.guild.get_member(kullanici_id)
        
        button.disabled = True
        for child in self.children:
            if child.custom_id == "yb_onay_butonu":
                self.remove_item(child)
                
        embed.color = discord.Color.red()
        embed.title = "❌ Yetkili Başvurusu Reddedildi"
        await interaction.message.edit(embed=embed, view=self)
        await interaction.followup.send("❌ Başvuru reddedildi olarak işaretlendi.", ephemeral=True)
        
        if uye:
            try:
                await uye.send("Maalesef, MTTS Yetkili başvurunuz yapılan değerlendirmeler sonucu olumsuz sonuçlanmıştır.")
            except:
                pass

class YetkiliBasvuruModal(Modal, title="MTTS Yetkili Başvuru Formu"):
    ad = TextInput(label="Adınız", placeholder="Örn: Ahmet", required=True)
    gorev = TextInput(label="İstediğiniz Görev", placeholder="Örn: Moderatör", required=True)
    aktiflik = TextInput(label="Haftalık Aktiflik Süreniz", placeholder="Örn: 20 Saat", required=True)
    deneyim = TextInput(label="Daha Önce Yetkili Oldunuz mu?", style=discord.TextStyle.paragraph, required=True)

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
    def __init__(self):
        super().__init__(timeout=None)

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
            embed = discord.Embed(title="Yeni Özel Rol Talebi!", color=discord.Color.blue())
            embed.add_field(name="Kullanıcı", value=interaction.user.mention, inline=True)
            embed.add_field(name="İstenen Rol", value=self.rol_label, inline=True)
            embed.add_field(name="İsim", value=self.ad.value, inline=True)
            embed.add_field(name="Sunucu", value=self.sunucu_adi.value, inline=True)
            embed.add_field(name="Link", value=self.sunucu_link.value, inline=False)
            embed.add_field(name="Detay", value=self.sunucu_det.value, inline=False)
            await log_kanali.send(embed=embed)
        await interaction.response.send_message("✅ Rol talebiniz alındı, yetkililer kontrol edecektir.", ephemeral=True)

class RolDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Sunucu Sahibi", value="sunucu", emoji="👑"),
            discord.SelectOption(label="Klan Sahibi", value="klan", emoji="⚔️"),
            discord.SelectOption(label="Hosting Sahibi", value="hosting", emoji="🖥️"),
            discord.SelectOption(label="İçerik Üreticisi", value="icerik", emoji="🎥")
        ]
        super().__init__(placeholder="Talep etmek istediğiniz rolü seçin", options=options, custom_id="rol_talep_dropdown")

    async def callback(self, interaction: discord.Interaction):
        rol_isimleri = {"sunucu": "Sunucu Sahibi", "klan": "Klan Sahibi", "hosting": "Hosting Sahibi", "icerik": "İçerik Üreticisi"}
        await interaction.response.send_modal(RolTalepModal(rol_label=rol_isimleri[self.values[0]]))

class RolBasvuruView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(RolDropdown())

# === 4. SLASH KOMUTLARI ===

@bot.tree.command(name="greet", description="Belirtilen kanala True/False seçimine göre @everyone etiketli reklam atar.")
@app_commands.checks.has_permissions(manage_messages=True)
@app_commands.describe(
    link="Reklamı yapılacak sunucunun davet linki (Örn: discord.gg/mtts)",
    aciklama="Reklam metni veya sunucu açıklaması",
    etiket_gitsin_mi="Everyone etiketi atılsın mı? True (Evet) / False (Hayır)"
)
async def slash_greet(interaction: discord.Interaction, link: str, aciklama: str, etiket_gitsin_mi: bool):
    hedef_kanal = interaction.guild.get_channel(REKLAM_KANAL_ID)
    
    if not hedef_kanal:
        await interaction.response.send_message("❌ Reklam kanalı bulunamadı! Lütfen REKLAM_KANAL_ID'yi kontrol edin.", ephemeral=True)
        return

    greet_yazisi = (
        f"**🌟 YENİ BİR PARTNER / REKLAM!**\n\n"
        f"📌 **Açıklama:** {aciklama}\n"
        f"🔗 **Katılmak İçin:** {link}\n\n"
        f"*Sunucumuza destekleri için teşekkür ederiz!*"
    )

    if etiket_gitsin_mi:
        greet_yazisi += "\n@everyone"

    await hedef_kanal.send(content=greet_yazisi)
    
    durum_mesaji = "Etiketli" if etiket_gitsin_mi else "Sessiz (Etiketsiz)"
    await interaction.response.send_message(f"✅ Greet reklamı {durum_mesaji} şekilde <#{REKLAM_KANAL_ID}> kanalına gönderildi!", ephemeral=True)

@bot.tree.command(name="paketler", description="Maden temalı güncel reklam paketlerinin listesini ve fiyatlarını gösterir.")
async def slash_paketler(interaction: discord.Interaction):
    sub_view = View()
    sub_view.add_item(ReklamPaketleriSubDropdown())
    await interaction.response.send_message("🔎 Detaylarını görmek istediğiniz MTTS Reklam Paketini seçin:", view=sub_view, ephemeral=True)

@bot.tree.command(name="reklam-hizmet-panel", description="Görseldeki MTTS Hizmetleri reklam başvuru panelini kurar.")
@app_commands.checks.has_permissions(administrator=True)
async def slash_reklam_hizmet_panel(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🤖 MTTS Hizmetleri",
        description="Aşağıdaki menüden paketleri inceleyebilirsiniz.",
        color=discord.Color.from_rgb(52, 152, 219)
    )
    await interaction.channel.send(embed=embed, view=HizmetlerPanelView())
    await interaction.response.send_message("Reklam hizmetleri paneli başarıyla kuruldu.", ephemeral=True)

@bot.tree.command(name="anket", description="Sunucuda oylama/anket başlatır.")
@app_commands.checks.has_permissions(manage_messages=True)
async def slash_anket(interaction: discord.Interaction, soru: str):
    embed = discord.Embed(title="📊 Yeni Anket / Oylama", description=soru, color=discord.Color.purple())
    embed.set_footer(text=f"Başlatan: {interaction.user.name}")
    await interaction.response.send_message("Anket oluşturuluyor...", ephemeral=True)
    msg = await interaction.channel.send(embed=embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")

@bot.tree.command(name="cekilis", description="Butonlu ve anlık sayaçlı lüks çekiliş düzenler.")
@app_commands.checks.has_permissions(manage_messages=True)
@app_commands.describe(sure="Çekiliş süresi (Örn: 30s, 10m, 2h, 6d)", odul="Çekiliş ödülü nedir? (Örn: 12 Aylık MC Premium)", kazanan_sayisi="Çekilişi kaç kişi kazanacak? (Varsayılan: 1)")
async def slash_cekilis(interaction: discord.Interaction, sure: str, odul: str, kazanan_sayisi: int = 1):
    saniye = parse_duration(sure)
    if saniye <= 0:
        await interaction.response.send_message("❌ Geçersiz süre formatı! Lütfen `30s`, `5m`, `2h` veya `6d` şeklinde girin.", ephemeral=True)
        return
    if kazanan_sayisi <= 0:
        await interaction.response.send_message("❌ Kazanan sayısı en az 1 olmalıdır!", ephemeral=True)
        return

    bitis_timestamp = int(time.time()) + saniye

    embed = discord.Embed(
        title=f"🎁 {odul} Çekilişi - Başladı!",
        description=f"Katılmak için aşağıdaki *Butona* tıklayın!\n\n"
                    f"•   Süre: <t:{bitis_timestamp}:R>\n"
                    f"•   Kazanan Sayısı: {kazanan_sayisi}\n"
                    f"•   Katılımcı Sayısı: 0",
        color=discord.Color.from_rgb(46, 204, 113)
    )
    
    await interaction.response.send_message("Çekiliş paneli kuruluyor...", ephemeral=True)
    
    cekilis_view = CekilisButonView(odul=odul, bitis_timestamp=bitis_timestamp, kazanan_sayisi=kazanan_sayisi)
    msg = await interaction.channel.send(embed=embed, view=cekilis_view)
    
    await asyncio.sleep(saniye)
    
    for item in cekilis_view.children:
        item.disabled = True
        
    katilanlar_listesi = list(cekilis_view.katilimcilar)
    
    if katilanlar_listesi:
        gercek_kazanan_sayisi = min(kazanan_sayisi, len(katilanlar_listesi))
        kazananlar = random.sample(katilanlar_listesi, k=gercek_kazanan_sayisi)
        kazanan_mentionlar = ", ".join([f"<@{k_id}>" for k_id in kazananlar])
        
        bitis_embed = discord.Embed(
            title=f"🎉 {odul} Çekilişi - Sona Erdi!",
            description=f"•   Kazananlar: {kazanan_mentionlar}\n"
                        f"•   Toplam Katılımcı: {len(katilanlar_listesi)}",
            color=discord.Color.red()
        )
        await msg.edit(embed=bitis_embed, view=cekilis_view)
        await interaction.channel.send(f"🎉 Tebrikler {kazanan_mentionlar}! **{odul}** çekilişini kazandınız!")
    else:
        iptal_embed = discord.Embed(
            title=f"❌ {odul} Çekilişi İptal Edildi",
            description="Çekilişe katılım olmadığı için kazanan seçilemedi.",
            color=discord.Color.greyple()
        )
        await msg.edit(embed=iptal_embed, view=cekilis_view)
        await interaction.channel.send(f"❌ **{odul}** çekilişine katılım olmadığı için kazanan seçilemedi.")

@bot.tree.command(name="destek-panel", description="Açılır Menülü Destek panelini kurar.")
@app_commands.checks.has_permissions(administrator=True)
async def slash_destek_panel(interaction: discord.Interaction):
    embed = discord.Embed(title="📥 Destek Menüsü", description="Aşağıdaki menüden destek talebi açabilirsiniz.", color=discord.Color.green())
    await interaction.channel.send(embed=embed, view=DestekPanelView())
    await interaction.response.send_message("Destek paneli kuruldu.", ephemeral=True)

@bot.tree.command(name="yetkili-basvuru-panel", description="Yetkili başvuru panelini kurar.")
@app_commands.checks.has_permissions(administrator=True)
async def slash_yb_panel(interaction: discord.Interaction):
    embed = discord.Embed(title="📋 Yetkili Başvuru Paneli", description="Aşağıdaki butona tıklayarak formu eksiksiz doldurunuz.", color=discord.Color.gold())
    await interaction.channel.send(embed=embed, view=YetkiliBasvuruView())
    await interaction.response.send_message("Yetkili başvuru paneli kuruldu.", ephemeral=True)

@bot.tree.command(name="rol-basvuru-panel", description="Özel rol başvuru panelini kurar.")
@app_commands.checks.has_permissions(administrator=True)
async def slash_rol_panel(interaction: discord.Interaction):
    embed = discord.Embed(title="👑 Özel Rol Başvuru Paneli", description="Aşağıdaki menüden seçim yapın ve formu doldurun.", color=discord.Color.blue())
    await interaction.channel.send(embed=embed, view=RolBasvuruView())
    await interaction.response.send_message("Rol başvuru paneli kuruldu.", ephemeral=True)

@bot.tree.command(name="lock", description="Kanalı kilitle.")
@app_commands.checks.has_permissions(manage_channels=True)
async def slash_lock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message(embed=discord.Embed(description="🔒 Bu kanal üyelerin yazışmasına **kapatılmıştır**.", color=discord.Color.red()))

@bot.tree.command(name="unlock", description="Kanal kilidini aç.")
@app_commands.checks.has_permissions(manage_channels=True)
async def slash_unlock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
    await interaction.response.send_message(embed=discord.Embed(description="🔓 Bu kanal üyelerin yazışmasına yeniden **açılmıştır**.", color=discord.Color.green()))

@bot.tree.command(name="sil", description="Mesaj siler.")
@app_commands.checks.has_permissions(administrator=True)
async def slash_sil(interaction: discord.Interaction, miktar: int):
    await interaction.response.defer(ephemeral=True)
    silinen = await interaction.channel.purge(limit=miktar)
    await interaction.followup.send(f"✅ {len(silinen)} adet mesaj silindi.", ephemeral=True)

@bot.tree.command(name="ilan-ver", description="İlan paylaşır.")
@app_commands.describe(urun="Ürün adı", fiyat="Fiyat", aciklama="Açıklama")
async def slash_ilan_ver(interaction: discord.Interaction, urun: str, fiyat: str, aciklama: str):
    embed = discord.Embed(
        title="Yeni İlan",
        color=discord.Color.orange()
    )
    embed.add_field(name="İlan Sahibi", value=interaction.user.mention, inline=False)
    embed.add_field(name="Ürün", value=urun, inline=True)
    embed.add_field(name="Fiyat", value=fiyat, inline=True)
    embed.add_field(name="Aciklama", value=aciklama, inline=False)
    embed.set_footer(text=f"İlan Tarihi: {time.strftime('%d/%m/%Y')}")
    
    await interaction.channel.send(embed=embed)
    await interaction.response.send_message("İlanın başarıyla paylaşıldı!", ephemeral=True)

# === BOT ON_READY KAYITLARI ===
@bot.event
async def on_ready():
    bot.add_view(DestekPanelView())
    bot.add_view(DestekKanalIciView())
    bot.add_view(YetkiliBasvuruView())
    bot.add_view(RolBasvuruView())
    bot.add_view(HizmetlerPanelView())
    bot.add_view(GreetMetniButonView())
    bot.add_view(YetkiliBasvuruIncelemeView())
    await bot.tree.sync()
    print("--- Tüm Greet ve Yetkili Onay/Red Sistemleri Kalıcı Olarak Aktif! ---")

keep_alive()
bot.run(os.environ.get("DISCORD_TOKEN"))
