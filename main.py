import discord
from discord.ext import commands, tasks
from discord.ui import View, Button, Select, Modal, TextInput
from discord import app_commands
import os
import asyncio
import random
import re
from datetime import datetime, timedelta
from flask import Flask
from threading import Thread

# === WEB SERVER (Render 7/24 Aktif Kalma Altyapısı) ===
app = Flask('')

@app.route('/')
def home(): 
    return f"Bot aktif! Son kontrol: {datetime.now().strftime('%H:%M:%S')}"

@app.route('/ping')
def ping(): 
    return "pong"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

Thread(target=run_web, daemon=True).start()

# === BOT AYARLARI ===
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True
bot = commands.Bot(command_prefix="!", intents=intents)

# === ID YAPILANDIRMALARI ===
GELEN_GIDEN_KANAL_ID = 1524866586475757704
BASVURU_KANAL_ID = 1524879141793435689
LOG_KANAL_ID = 1524879141793435689
PAZAR_KANAL_ID = 1524866586912227330
SUPPORT_ROL_ID = 1524866585637031961

# === BANNER / LOGO URL (MTTS Tasarımı) ===
BANNER_URL = "https://images-ext-1.discordapp.net/external/re_m7v0e0_tA83Yw_4X2A2r3V8M/https/cdn.discordapp.com/attachments/1258071850123530341/1260613271783440465/image_42fd48.png"

ROL_IDLERI = {
    "Sunucu Sahibi": 1524866585637031962,   
    "Klan Sahibi": 1524866585637031963,
    "Hosting Sahibi": 1524866585637031964,
    "İçerik Üreticisi": 1524866585637031965
}

TICKET_KATEGORILERI = {
    "partnerlik": ("📃", "partnerlik"),
    "sikayet": ("🚨", "şikayet"),
    "yetkili-basvuru": ("📙", "yetkili başvurusu"),
    "reklam": ("💵", "reklam"),
    "genel": ("📜", "genel")
}

# =====================================================================
# === 1. GELİŞMİŞ HATA ÖNLEYİCİ ÇEKİLİŞ SİSTEMİ ===
# =====================================================================

class CekilisKatilView(View):
    def __init__(self, odul: str, bitis_zamani: datetime, kazanan_sayisi: int):
        super().__init__(timeout=None)
        self.odul = odul
        self.bitis_zamani = bitis_zamani
        self.kazanan_sayisi = kazanan_sayisi
        self.katilimcilar = set()

    @discord.ui.button(label="", style=discord.ButtonStyle.primary, emoji="🎉", custom_id="cekilis_katil_btn")
    async def katil(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.defer(ephemeral=True)
        user_id = interaction.user.id
        if user_id in self.katilimcilar:
            self.katilimcilar.remove(user_id)
            await interaction.followup.send("❌ Çekilişten katılımınızı çektiniz.", ephemeral=True)
        else:
            self.katilimcilar.add(user_id)
            await interaction.followup.send("🎉 Çekilişe başarıyla katıldınız! Bol şans.", ephemeral=True)
            
        try:
            embed = interaction.message.embeds[0]
            embed.set_field_at(2, name="• Katılımcı Sayısı", value=str(len(self.katilimcilar)), inline=False)
            await interaction.message.edit(embed=embed)
        except Exception:
            pass

def parse_duration(duration_str: str) -> int:
    match = re.match(r"^(\d+)([smhd])$", duration_str.lower())
    if not match: return None
    amount, unit = match.groups()
    amount = int(amount)
    if unit == 's': return amount
    elif unit == 'm': return amount * 60
    elif unit == 'h': return amount * 3600
    elif unit == 'd': return amount * 86400
    return None

# =====================================================================
# === 2. Gelişmiş ROL BAŞVURU SİSTEMİ ===
# =====================================================================

class RolKararView(View):
    def __init__(self, basvuran_id: int, rol_adi: str):
        super().__init__(timeout=None)
        self.basvuran_id = basvuran_id
        self.rol_adi = rol_adi

    @discord.ui.button(label="Onayla", style=discord.ButtonStyle.success, emoji="✅", custom_id="basvuru_onayla_btn")
    async def onayla(self, interaction: discord.Interaction, button: discord.Button):
        support_rol = interaction.guild.get_role(SUPPORT_ROL_ID)
        if not (interaction.user.guild_permissions.administrator or (support_rol and support_rol in interaction.user.roles)):
            await interaction.response.send_message("❌ Bu başvuruyu onaylamak için yetkiniz yok!", ephemeral=True)
            return

        await interaction.response.defer()
        guild = interaction.guild
        member = guild.get_member(self.basvuran_id)
        hedef_rol_id = ROL_IDLERI.get(self.rol_adi)
        hedef_rol = guild.get_role(hedef_rol_id) if hedef_rol_id else None

        rol_durumu = "Rol otomatik tanımlandı."
        if member and hedef_rol:
            try: await member.add_roles(hedef_rol)
            except Exception: rol_durumu = "Rol tanımlanırken yetki hatası oluştu."
        else:
            rol_durumu = "Kullanıcı bulunamadı veya rol geçersiz."

        eski_embed = interaction.message.embeds[0]
        yeni_embed = discord.Embed(title=eski_embed.title, color=discord.Color.green(), timestamp=eski_embed.timestamp)
        
        for field in eski_embed.fields:
            if field.name == "Durum": yeni_embed.add_field(name="Durum", value="✅ Onaylandı", inline=False)
            else: yeni_embed.add_field(name=field.name, value=field.value, inline=False)
                
        yeni_embed.add_field(name="İşlem Yapan Yetkili", value=f"{interaction.user.mention}", inline=False)
        yeni_embed.set_footer(text=f"{rol_durumu} • Kullanıcı ID: {self.basvuran_id}")
        await interaction.message.edit(embed=yeni_embed, view=None)
        
        if member:
            try: await member.send(f"🎉 **{interaction.guild.name}** sunucusundaki **{self.rol_adi}** başvurunuz onaylandı!")
            except discord.Forbidden: pass

    @discord.ui.button(label="Reddet", style=discord.ButtonStyle.danger, emoji="❌", custom_id="basvuru_reddet_btn")
    async def reddet(self, interaction: discord.Interaction, button: discord.Button):
        support_rol = interaction.guild.get_role(SUPPORT_ROL_ID)
        if not (interaction.user.guild_permissions.administrator or (support_rol and support_rol in interaction.user.roles)):
            await interaction.response.send_message("❌ Bu başvuruyu reddetmek için yetkiniz yok!", ephemeral=True)
            return

        class RedGerekceModal(Modal, title="Başvuru Reddetme Sebebi"):
            sebep = TextInput(label="Reddetme Detayları / Sebebi", placeholder="Gerekçe giriniz...", required=True)
            def __init__(self, basvuran_id, rol_adi, orijinal_mesaj):
                super().__init__()
                self.basvuran_id = basvuran_id
                self.rol_adi = rol_adi
                self.orijinal_mesaj = orijinal_mesaj

            async def on_submit(self, modal_interaction: discord.Interaction):
                await modal_interaction.response.defer()
                eski_embed = self.orijinal_mesaj.embeds[0]
                yeni_embed = discord.Embed(title=eski_embed.title, color=discord.Color.red(), timestamp=eski_embed.timestamp)

                for field in eski_embed.fields:
                    if field.name == "Durum": yeni_embed.add_field(name="Durum", value="❌ Reddedildi", inline=False)
                    else: yeni_embed.add_field(name=field.name, value=field.value, inline=False)

                yeni_embed.add_field(name="Detaylar", value=self.sebep.value, inline=False)
                yeni_embed.add_field(name="İşlem Yapan Yetkili", value=f"{modal_interaction.user.mention}", inline=False)
                yeni_embed.set_footer(text=f"Başvuru Reddedildi • Kullanıcı ID: {self.basvuran_id}")
                await self.orijinal_mesaj.edit(embed=yeni_embed, view=None)

                member = modal_interaction.guild.get_member(self.basvuran_id)
                if member:
                    try: await member.send(f"❌ **{modal_interaction.guild.name}** sunucusundaki **{self.rol_adi}** başvurunuz reddedildi.\n**Sebep:** {self.sebep.value}")
                    except discord.Forbidden: pass

        await interaction.response.send_modal(RedGerekceModal(self.basvuran_id, self.rol_adi, interaction.message))

class RolBasvuruModal(Modal):
    def __init__(self, rol_adi: str):
        super().__init__(title=f"{rol_adi} Başvuru Formu")
        self.rol_adi = rol_adi
        self.proje_adi = TextInput(label="Proje Adı", placeholder="Örn: MC TexturePack", required=True)
        self.kanit_linki = TextInput(label="Kanıt Linki", placeholder="Örn: discord.gg/textures", required=True)
        self.add_item(self.proje_adi)
        self.add_item(self.kanit_linki)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        basvuru_kanali = interaction.guild.get_channel(BASVURU_KANAL_ID)
        if not basvuru_kanali:
            await interaction.followup.send("❌ Başvuru kanalı bulunamadı!", ephemeral=True)
            return

        suan = datetime.now()
        embed = discord.Embed(title=f"{self.rol_adi} Başvurusu", color=discord.Color.from_rgb(241, 196, 15), timestamp=suan)
        embed.add_field(name="Başvuran", value=interaction.user.mention, inline=False)
        embed.add_field(name="Rol", value=self.rol_adi, inline=False)
        embed.add_field(name="Proje Adı", value=self.proje_adi.value, inline=False)
        embed.add_field(name="Kanıt Linki", value=self.kanit_linki.value, inline=False)
        embed.add_field(name="Durum", value="⌛ Beklemede...", inline=False)
        embed.add_field(name="Başvuru Tarihi", value=suan.strftime("%d/%m/%Y %H:%M"), inline=False)
        embed.set_footer(text=f"Kullanıcı ID: {interaction.user.id}")

        view = RolKararView(basvuran_id=interaction.user.id, rol_adi=self.rol_adi)
        await basvuru_kanali.send(embed=embed, view=view)
        await interaction.followup.send("✅ Başvurunuz başarıyla yetkililere iletildi!", ephemeral=True)

class RolBasvuruView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Sunucu Sahibi", style=discord.ButtonStyle.primary, emoji="👑", custom_id="basvuru_sunucu_sahibi")
    async def sunucu_sahibi(self, interaction: discord.Interaction, button: discord.Button): 
        try: await interaction.response.send_modal(RolBasvuruModal("Sunucu Sahibi"))
        except Exception: pass
    @discord.ui.button(label="Klan Sahibi", style=discord.ButtonStyle.primary, emoji="⚔️", custom_id="basvuru_klan_sahibi")
    async def klan_sahibi(self, interaction: discord.Interaction, button: discord.Button): 
        try: await interaction.response.send_modal(RolBasvuruModal("Klan Sahibi"))
        except Exception: pass
    @discord.ui.button(label="Hosting Sahibi", style=discord.ButtonStyle.primary, emoji="💻", custom_id="basvuru_hosting_sahibi")
    async def hosting_sahibi(self, interaction: discord.Interaction, button: discord.Button): 
        try: await interaction.response.send_modal(RolBasvuruModal("Hosting Sahibi"))
        except Exception: pass
    @discord.ui.button(label="İçerik Üreticisi", style=discord.ButtonStyle.primary, emoji="🎬", custom_id="basvuru_icerik_ureticisi")
    async def icerik_ureticisi(self, interaction: discord.Interaction, button: discord.Button): 
        try: await interaction.response.send_modal(RolBasvuruModal("İçerik Üreticisi"))
        except Exception: pass

# =====================================================================
# === 3. DESTEK (TICKET) SİSTEMİ ===
# =====================================================================

class TicketIciAksiyonView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Kapat", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="ticket_kapat_btn")
    async def kapat(self, interaction: discord.Interaction, button: discord.Button):
        support_rol = interaction.guild.get_role(SUPPORT_ROL_ID)
        if interaction.user.guild_permissions.administrator or (support_rol and support_rol in interaction.user.roles):
            await interaction.response.send_message("⚙️ Destek talebi 5 saniye içerisinde kalıcı olarak kapatılıyor...")
            await asyncio.sleep(5)
            await interaction.channel.delete()
        else:
            await interaction.response.send_message("❌ Bu işlem için yetkiniz bulunmuyor!", ephemeral=True)

    @discord.ui.button(label="Aktif Yetkililer", style=discord.ButtonStyle.primary, emoji="👤", custom_id="ticket_yetkililer_btn")
    async def yetkililer(self, interaction: discord.Interaction, button: discord.Button):
        support_rol = interaction.guild.get_role(SUPPORT_ROL_ID)
        embed = discord.Embed(title="🛡️ Aktif Destek Ekibi", color=discord.Color.blue())
        if support_rol:
            aktifler = [m.mention for m in support_rol.members if m.status != discord.Status.offline]
            embed.description = "Şu an çevrimiçi olan yetkililer:\n" + ", ".join(aktifler) if aktifler else "Şu an aktif yetkili bulunmuyor."
        else: embed.description = "Destek rolü sunucuda bulunamadı."
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Yardım Al", style=discord.ButtonStyle.success, emoji="🆘", custom_id="ticket_yardim_btn")
    async def yardim_al(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.send_message("🛎️ Destek ekibine acil durum bildirimi geçildi.", ephemeral=True)

class DestekGirisModal(Modal, title="Destek Talebi Formu"):
    konu = TextInput(label="Talep Konusu / Gerekçeniz", placeholder="Örn: Partnerlik isteği", required=True)
    def __init__(self, kategori_key):
        super().__init__()
        self.kategori_key = kategori_key

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        user = interaction.user
        emoji, kategori_adi = TICKET_KATEGORILERI[self.kategori_key]
        
        support_rol = guild.get_role(SUPPORT_ROL_ID)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        if support_rol: overwrites[support_rol] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        channel = await guild.create_text_channel(name=f"ticket-{user.name}", overwrites=overwrites)
        suan = datetime.now()

        embed = discord.Embed(color=discord.Color.from_rgb(88, 101, 242))
        embed.set_author(name="📑 Destek Talebi")
        embed.description = f"📌 **Konu**\n{self.konu.value}\n\n📂 **Kategori**\n{kategori_adi}\n\n👤 **Kullanıcı**\n{user.name}\n\n⏱️ **Açılış Zamanı**\n{suan.strftime('%d %B %Y %H:%M')}"
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text=f"Ticket ID: {random.randint(1000,9999)}")

        if support_rol: await channel.send(content=f"{user.mention}, {support_rol.mention}", embed=embed, view=TicketIciAksiyonView())
        else: await channel.send(content=f"{user.mention}", embed=embed, view=TicketIciAksiyonView())
        await interaction.followup.send(f"✅ Destek odanız oluşturuldu: {channel.mention}", ephemeral=True)

class PanelKategoriDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Partnerlik", value="partnerlik", emoji="📃"),
            discord.SelectOption(label="Şikayet", value="sikayet", emoji="🚨"),
            discord.SelectOption(label="Yetkili Başvurusu", value="yetkili-basvuru", emoji="📙"),
            discord.SelectOption(label="Reklam", value="reklam", emoji="💵"),
            discord.SelectOption(label="Genel", value="genel", emoji="📜")
        ]
        super().__init__(placeholder="📌 Bir destek kategorisi seçin", min_values=1, max_values=1, options=options, custom_id="panel_dropdown")
    async def callback(self, interaction: discord.Interaction): await interaction.response.send_modal(DestekGirisModal(self.values[0]))

class PanelAnaView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(PanelKategoriDropdown())

# =====================================================================
# === 4. TÜRKÇE KARAKTERSİZ GLOBAL SLASH KOMUTLARI ===
# =====================================================================

@bot.tree.command(name="cekilis", description="Canlı butonlu bir çekiliş başlatır (Yönetici).")
@app_commands.checks.has_permissions(administrator=True)
async def slash_cekilis(interaction: discord.Interaction, süre: str, ödül: str, kazananlar: int = 1):
    await interaction.response.defer(ephemeral=True)
    saniye = parse_duration(süre)
    if saniye is None:
        await interaction.followup.send("❌ Hatalı süre formatı! Örnek: `10m`, `2h`, `1d`", ephemeral=True)
        return

    bitis_zamani = datetime.utcnow() + timedelta(seconds=saniye)
    embed = discord.Embed(title=f"🎁 {ödül} - Başladı!", description="Katılmak için aşağıdaki *Butona* tıklayın!", color=discord.Color.from_rgb(46, 204, 113))
    embed.add_field(name="• Süre", value=f"<t:{int(bitis_zamani.timestamp())}:R>", inline=False)
    embed.add_field(name="• Kazanan Sayısı", value=str(kazananlar), inline=False)
    embed.add_field(name="• Katılımcı Sayısı", value="0", inline=False)
    
    if 'BANNER_URL' in globals() and BANNER_URL.startswith("http"): embed.set_image(url=BANNER_URL)

    view = CekilisKatilView(odul=ödül, bitis_zamani=bitis_zamani, kazanan_sayisi=kazananlar)
    cekilis_mesaj = await interaction.channel.send(embed=embed, view=view)
    await interaction.followup.send("✅ Çekiliş başlatıldı!", ephemeral=True)
    
    await asyncio.sleep(saniye)
    try: taze_mesaj = await interaction.channel.fetch_message(cekilis_mesaj.id)
    except discord.NotFound: return

    katilimci_listesi = list(view.katilimcilar)
    if len(katilimci_listesi) == 0:
        son_embed = discord.Embed(title=f"🎁 {ödül} - Sona Erdi", description="Yetersiz katılım.", color=discord.Color.red())
        await taze_mesaj.edit(embed=son_embed, view=None)
    else:
        gercek_kazananlar = random.sample(katilimci_listesi, min(len(katilimci_listesi), kazananlar))
        kazanan_mentionlar = ", ".join([f"<@{uid}>" for uid in gercek_kazananlar])
        
        son_embed = discord.Embed(title=f"🎁 {ödül} - Sona Erdi!", color=discord.Color.from_rgb(46, 204, 113))
        son_embed.add_field(name="• Ödül", value=ödül, inline=False)
        son_embed.add_field(name="• Kazananlar", value=kazanan_mentionlar, inline=False)
        son_embed.add_field(name="• Toplam Katılımcı", value=str(len(katilimci_listesi)), inline=False)
        
        await taze_mesaj.edit(embed=son_embed, view=None)
        await interaction.channel.send(f"🎉 Tebrikler {kazanan_mentionlar}! **{ödül}** kazandınız!")

@bot.tree.command(name="rol-basvuru", description="Unvan doğrulama başvuru panelini gönderir (Yönetici).")
@app_commands.checks.has_permissions(administrator=True)
async def slash_rol_basvuru(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    embed = discord.Embed(title="Unvan Doğrulama Başvuruları", description="Gerekli unvan rollerini talep etmek için aşağıdaki butonları kullanın.", color=discord.Color.from_rgb(88, 101, 242))
    if 'BANNER_URL' in globals() and BANNER_URL.startswith("http"): embed.set_image(url=BANNER_URL)
    await interaction.channel.send(embed=embed, view=RolBasvuruView())
    await interaction.followup.send("✅ Rol Başvuru paneli kuruldu!", ephemeral=True)

@bot.tree.command(name="destek-panel", description="Dış destek panelini oluşturur (Yönetici).")
@app_commands.checks.has_permissions(administrator=True)
async def slash_destek_panel(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    embed = discord.Embed(title="📥 Destek Menüsü", description="Lütfen destek almak istediğiniz kategoriyi aşağıdaki menüden seçin.", color=discord.Color.from_rgb(88, 101, 242))
    if 'BANNER_URL' in globals() and BANNER_URL.startswith("http"): embed.set_image(url=BANNER_URL)
    await interaction.channel.send(embed=embed, view=PanelAnaView())
    await interaction.followup.send("✅ Destek paneli kuruldu!", ephemeral=True)

@bot.tree.command(name="sil", description="Mesajları temizler (Yönetici).")
@app_commands.checks.has_permissions(administrator=True)
async def slash_sil(interaction: discord.Interaction, miktar: int):
    await interaction.response.defer(ephemeral=True)
    await interaction.channel.purge(limit=miktar)
    await interaction.followup.send("🗑️ Temizlendi.", ephemeral=True)

# =====================================================================
# === 5. SİSTEMSEL EVENTLER (GELEN - GİDEN) ===
# =====================================================================

@bot.event
async def on_member_join(member):
    channel = member.guild.get_channel(GELEN_GIDEN_KANAL_ID)
    if channel:
        embed = discord.Embed(title="📥 Sunucuya Katıldı!", description=f"{member.mention} aramıza hoş geldin! **{len(member.guild.members)}** kişiyiz.", color=discord.Color.green())
        embed.set_thumbnail(url=member.display_avatar.url)
        await channel.send(embed=embed)

@bot.event
async def on_member_remove(member):
    channel = member.guild.get_channel(GELEN_GIDEN_KANAL_ID)
    if channel:
        embed = discord.Embed(title="📤 Sunucudan Ayrıldı...", description=f"{member.name} ayrıldı. **{len(member.guild.members)}** kişi kaldık.", color=discord.Color.red())
        await channel.send(embed=embed)

@bot.event
async def on_ready():
    print(f"Bot sorunsuzca aktif: {bot.user}")
    bot.add_view(PanelAnaView())
    bot.add_view(RolBasvuruView())
    bot.add_view(TicketIciAksiyonView())
    
    # KESİN ÇÖZÜM: Komutları küresel (global) olarak senkronize ediyoruz.
    try:
        await bot.tree.sync()
        print("Tüm global slash komutları Discord API'sine başarıyla işlendi!")
    except Exception as e: 
        print(f"Senkronizasyon Hatası: {e}")

TOKEN = os.environ.get('DISCORD_TOKEN', '')
if TOKEN: 
    bot.run(TOKEN, reconnect=True)
