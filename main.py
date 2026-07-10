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
import urllib.request

# === WEB SERVER ===
app = Flask('')
@app.route('/')
def home(): return f"Bot aktif! {datetime.now().strftime('%H:%M:%S')}"
@app.route('/ping')
def ping(): return "pong"
def run_web(): app.run(host='0.0.0.0', port=8080)
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

# === MTTS GÖRSEL LOGO URL ===
BANNER_URL = "https://images-ext-1.discordapp.net/external/re_m7v0e0_tA83Yw_4X2A2r3V8M/https/cdn.discordapp.com/attachments/..." 

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
# === GELİŞMİŞ BUTONLU ÇEKİLİŞ SİSTEMİ ===
# =====================================================================

class CekilisKatilView(View):
    def __init__(self, odul: str, bitis_zamani: datetime, kazanan_sayisi: int):
        super().__init__(timeout=None)
        self.odul = odul
        self.bitis_zamani = bitis_zamani
        self.kazanan_sayisi = kazanan_sayisi
        self.katilimcilar = set()  # Benzersiz katılımcı ID'lerini tutar

    @discord.ui.button(label="", style=discord.ButtonStyle.primary, emoji="🎉", custom_id="cekilis_katil_btn")
    async def katil(self, interaction: discord.Interaction, button: discord.Button):
        user_id = interaction.user.id
        
        # Eğer kullanıcı zaten katıldıysa katılımı iptal et, katılmadıysa ekle
        if user_id in self.katilimcilar:
            self.katilimcilar.remove(user_id)
            await interaction.response.send_message("❌ Çekilişten katılımınızı çektiniz.", ephemeral=True)
        else:
            self.katilimcilar.add(user_id)
            await interaction.response.send_message("🎉 Çekilişe başarıyla katıldınız! Bol şans.", ephemeral=True)
            
        # Embed üzerindeki Katılımcı Sayısı bilgisini canlı güncelle
        embed = interaction.message.embeds[0]
        # Katılımcı sayısını güncelliyoruz
        embed.set_field_at(2, name="• Katılımcı Sayısı", value=str(len(self.katilimcilar)), inline=False)
        await interaction.message.edit(embed=embed)

# Süre formatını çözümleme (örn: 5m -> 300 saniye)
def parse_duration(duration_str: str) -> int:
    match = re.match(r"^(\d+)([smhd])$", duration_str.lower())
    if not match:
        return None
    amount, unit = match.groups()
    amount = int(amount)
    
    if unit == 's':
        return amount
    elif unit == 'm':
        return amount * 60
    elif unit == 'h':
        return amount * 3600
    elif unit == 'd':
        return amount * 86400
    return None

# =====================================================================
# === ROL BAŞVURU SİSTEMİ ===
# =====================================================================

class RolBasvuruModal(Modal):
    def __init__(self, rol_adi: str):
        super().__init__(title=f"{rol_adi} Başvuru Formu")
        self.rol_adi = rol_adi
        
        self.bilgi = TextInput(
            label="Kendinizi Tanıtın / Detaylar", 
            style=discord.TextStyle.paragraph,
            placeholder="Neden bu rolü talep ediyorsunuz? Kanıt veya detay sununuz.",
            required=True
        )
        self.add_item(self.bilgi)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        basvuru_kanali = interaction.guild.get_channel(BASVURU_KANAL_ID)
        if not basvuru_kanali:
            await interaction.followup.send("❌ Başvuru kanalı bulunamadı! Lütfen geliştiriciyle iletişime geçin.", ephemeral=True)
            return

        embed = discord.Embed(
            title="📥 Yeni Unvan Başvurusu!",
            color=discord.Color.gold(),
            timestamp=datetime.now()
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.add_field(name="👤 Başvuran", value=f"{interaction.user.mention} ({interaction.user.name})", inline=False)
        embed.add_field(name="🏷️ Talep Edilen Rol", value=f"**{self.rol_adi}**", inline=False)
        embed.add_field(name="📝 Açıklama / Kanıt", value=self.bilgi.value, inline=False)
        embed.set_footer(text=f"Kullanıcı ID: {interaction.user.id}")

        await basvuru_kanali.send(embed=embed)
        await interaction.followup.send("✅ Başvurunuz başarıyla yetkililere iletildi. En kısa sürede inceelenecektir!", ephemeral=True)

class RolBasvuruView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Sunucu Sahibi", style=discord.ButtonStyle.primary, emoji="👑", custom_id="basvuru_sunucu_sahibi")
    async def sunucu_sahibi(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.send_modal(RolBasvuruModal("Sunucu Sahibi"))

    @discord.ui.button(label="Klan Sahibi", style=discord.ButtonStyle.primary, emoji="⚔️", custom_id="basvuru_klan_sahibi")
    async def klan_sahibi(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.send_modal(RolBasvuruModal("Klan Sahibi"))

    @discord.ui.button(label="Hosting Sahibi", style=discord.ButtonStyle.primary, emoji="💻", custom_id="basvuru_hosting_sahibi")
    async def hosting_sahibi(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.send_modal(RolBasvuruModal("Hosting Sahibi"))

    @discord.ui.button(label="İçerik Üreticisi", style=discord.ButtonStyle.primary, emoji="🎬", custom_id="basvuru_icerik_ureticisi")
    async def icerik_ureticisi(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.send_modal(RolBasvuruModal("İçerik Üreticisi"))

# =====================================================================
# === TICKET SİSTEMİ ===
# =====================================================================

class TicketIciAksiyonView(View):
    def __init__(self):
        super().__init__(timeout=None)

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
        else:
            embed.description = "Destek rolü sunucuda bulunamadı."
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Yardım Al", style=discord.ButtonStyle.success, emoji="🆘", custom_id="ticket_yardim_btn")
    async def yardim_al(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.send_message("🛎️ Destek ekibine acil durum bildirimi geçildi. En kısa sürede yanıt alacaksınız.", ephemeral=True)

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
        if support_rol:
            overwrites[support_rol] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        channel = await guild.create_text_channel(name=f"ticket-{user.name}", overwrites=overwrites)
        
        suan = datetime.now()
        tarih_str = suan.strftime("%d %B %Y %H:%M")
        ticket_id = random.randint(1000000000, 9999999999)

        embed = discord.Embed(color=discord.Color.from_rgb(88, 101, 242))
        embed.set_author(name="📑 Destek Talebi")
        embed.description = "Destek ekibimiz en kısa sürede size yardımcı olacaktır.\n\n" \
                            f"📌 **Konu**\n{self.konu.value}\n\n" \
                            f"📂 **Kategori**\n{kategori_adi} \n\n" \
                            f"👤 **Kullanıcı**\n{user.name}\n\n" \
                            f"🆔 **Kullanıcı ID**\n{user.id}\n\n" \
                            f"⏱️ **Açılış Zamanı**\n{tarih_str}"
        
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text=f"Ticket ID: {ticket_id} • bugün saat {suan.strftime('%H:%M')}")

        if support_rol:
            await channel.send(content=f"{user.mention}, destek talebiniz açıldı. {support_rol.mention}", embed=embed, view=TicketIciAksiyonView())
        else:
            await channel.send(content=f"{user.mention}, destek talebiniz açıldı.", embed=embed, view=TicketIciAksiyonView())
            
        await interaction.followup.send(f"✅ Destek odanız başarıyla oluşturuldu: {channel.mention}", ephemeral=True)

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

    async def callback(self, interaction: discord.Interaction):
        kategori_key = self.values[0]
        await interaction.response.send_modal(DestekGirisModal(kategori_key))

class PanelAnaView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(PanelKategoriDropdown())

# =====================================================================
# === KOMUTLAR VE TETİKLEYİCİLER ===
# =====================================================================

# === YENİ: GÖRSELDEKİ ÇEKİLİŞ KOMUTU ===
@bot.tree.command(name="çekiliş", description="Canlı butonlu bir çekiliş başlatır (Yönetici).")
@app_commands.checks.has_permissions(administrator=True)
async def slash_cekilis(interaction: discord.Interaction, süre: str, ödül: str, kazananlar: int = 1):
    await interaction.response.defer(ephemeral=True)
    
    saniye = parse_duration(süre)
    if saniye is None:
        await interaction.followup.send("❌ Hatalı süre formatı! Örnekler: `30s` (30 saniye), `10m` (10 dakika), `2h` (2 saat), `1d` (1 gün)", ephemeral=True)
        return

    # Zaman hesaplamaları
    bitis_zamani = datetime.utcnow() + timedelta(seconds=saniye)
    timestamp_milis = int(bitis_zamani.timestamp())
    
    # Görseldeki birebir tasarım şablonu (Yeşilimsi sol çizgi)
    embed = discord.Embed(
        title=f"🎁 {ödül} - Başladı!",
        description="Katılmak için aşağıdaki *Butona* tıklayın!",
        color=discord.Color.from_rgb(46, 204, 113) # Açık Yeşil tonları
    )
    # <t:timestamp:R> Discord'un kendi dinamik canlı süre sayacıdır.
    embed.add_field(name="• Süre", value=f"<t:{timestamp_milis}:R>", inline=False)
    embed.add_field(name="• Kazanan Sayısı", value=str(kazananlar), inline=False)
    embed.add_field(name="• Katılımcı Sayısı", value="0", inline=False)
    
    if 'BANNER_URL' in globals() and BANNER_URL.startswith("http") and not BANNER_URL.endswith("..."):
         embed.set_thumbnail(url=BANNER_URL)

    # Butonlu görünümü oluştur ve kanala gönder
    view = CekilisKatilView(odul=ödül, bitis_zamani=bitis_zamani, kazanan_sayisi=kazananlar)
    cekilis_mesaj = await interaction.channel.send(embed=embed, view=view)
    await interaction.followup.send("✅ Çekiliş başarıyla başlatıldı!", ephemeral=True)
    
    # Çekiliş süresini bekle
    await asyncio.sleep(saniye)
    
    # Süre dolduğunda yeni mesaj bilgilerini çek
    try:
        taze_mesaj = await interaction.channel.fetch_message(cekilis_mesaj.id)
    except discord.NotFound:
        return  # Çekiliş mesajı silinmişse işlemi iptal et

    # Kazananları belirle
    katilimci_listesi = list(view.katilimcilar)
    
    if len(katilimci_listesi) == 0:
        # Katılımcı yoksa bitiş durumunu güncelle
        son_embed = discord.Embed(
            title=f"🎁 {ödül} - Sona Erdi",
            description="Maalesef çekilişe yeterli katılım sağlanmadı.",
            color=discord.Color.red()
        )
        son_embed.add_field(name="• Kazananlar", value="Katılımcı bulunamadı 😢", inline=False)
        await taze_mesaj.edit(embed=son_embed, view=None)
        await interaction.channel.send(f"⚠️ **{ödül}** çekilişine kimse katılmadığı için kazanan belirlenemedi.")
    else:
        # Kazananları rastgele seç
        gercek_kazanan_sayisi = min(len(katilimci_listesi), kazananlar)
        kazananlar_listesi = random.sample(katilimci_listesi, gercek_kazanan_sayisi)
        kazanan_mentionlar = ", ".join([f"<@{uid}>" for uid in kazananlar_listesi])
        
        # Tamamlanmış Embed Görünümü
        son_embed = discord.Embed(
            title=f"🎁 {ödül} - Sona Erdi!",
            description="Tebrikler! Kazanan şanslı üyelerimiz aşağıda listelenmiştir.",
            color=discord.Color.from_rgb(46, 204, 113)
        )
        son_embed.add_field(name="• Ödül", value=ödül, inline=False)
        son_embed.add_field(name="• Kazananlar", value=kazanan_mentionlar, inline=False)
        son_embed.add_field(name="• Toplam Katılımcı", value=str(len(katilimci_listesi)), inline=False)
        
        if 'BANNER_URL' in globals() and BANNER_URL.startswith("http") and not BANNER_URL.endswith("..."):
             son_embed.set_thumbnail(url=BANNER_URL)
             
        # Çekiliş mesajını güncelle (butonları devredışı bırak/sil)
        await taze_mesaj.edit(embed=son_embed, view=None)
        
        # Kanala tebrik mesajı gönder
        await interaction.channel.send(f"🎉 Tebrikler {kazanan_mentionlar}! **{ödül}** kazandınız!")


@bot.tree.command(name="rol-basvuru", description="Unvan doğrulama başvuru panelini gönderir (Yönetici).")
@app_commands.checks.has_permissions(administrator=True)
async def slash_rol_basvuru(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    
    embed = discord.Embed(
        title="Unvan Doğrulama Başvuruları",
        description="Sunucu sahibi, klan lideri, hosting firması veya içerik üreticisi unvanlarına sahipseniz rollerinizi teslim almak için aşağıdaki butonlara tıklayın.",
        color=discord.Color.from_rgb(88, 101, 242)
    )
    
    if 'BANNER_URL' in globals() and BANNER_URL.startswith("http") and not BANNER_URL.endswith("..."):
        embed.set_thumbnail(url=BANNER_URL)
    else:
        if interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)

    try:
        await interaction.channel.send(embed=embed, view=RolBasvuruView())
        await interaction.followup.send("✅ Rol Başvuru paneli bu kanala başarıyla kuruldu!", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Panel kurulurken hata oluştu! Hata: `{e}`", ephemeral=True)


@bot.tree.command(name="destek-panel", description="Dış destek panelini MTTS logosuyla oluşturur (Yönetici).")
@app_commands.checks.has_permissions(administrator=True)
async def slash_destek_panel(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    
    embed = discord.Embed(
        title="📥 Destek Menüsü",
        description="Aşağıdaki menüden destek talebi açabilirsiniz.\n\n"
                    "**• Yetkilileri meşgul etmek yasaktır.**\n"
                    "**• Destek taleplerinizi kategorilere göre açın.**\n"
                    "**• Uygun kanal seçildikten sonra destek ekibi bilgilendirilecektir.**\n\n"
                    "Bir kategori seçerek destek talebi açabilirsiniz. • " + datetime.now().strftime("%d.%m.%Y %H:%M"),
        color=discord.Color.from_rgb(88, 101, 242)
    )
    
    if 'BANNER_URL' in globals() and BANNER_URL.startswith("http") and not BANNER_URL.endswith("..."):
        embed.set_thumbnail(url=BANNER_URL)
    else:
        if interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)
    
    try:
        await interaction.channel.send(embed=embed, view=PanelAnaView())
        await interaction.followup.send("✅ Panel başarıyla bu kanala kuruldu!", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Panel gönderilirken hata oluştu! Hata: `{e}`", ephemeral=True)


@bot.tree.command(name="selam", description="Sunucudakilere selam verir.")
async def slash_selam(interaction: discord.Interaction):
    await interaction.response.send_message(f"Selam {interaction.user.mention}! Hoş geldin. 👋")

@bot.tree.command(name="ping", description="Botun anlık gecikme süresini gösterir.")
async def slash_ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"🏓 Pong! Gecikme: `{round(bot.latency * 1000)}ms`")

@bot.tree.command(name="sil", description="Mesajları temizler (Yönetici).")
@app_commands.checks.has_permissions(administrator=True)
async def slash_sil(interaction: discord.Interaction, miktar: int):
    await interaction.response.defer(ephemeral=True)
    await interaction.channel.purge(limit=miktar)
    await interaction.followup.send("🗑️ Temizlendi.", ephemeral=True)


# === KESİN ÇALIŞAN GELEN - GİDEN SİSTEMİ ===
@bot.event
async def on_member_join(member):
    channel = member.guild.get_channel(GELEN_GIDEN_KANAL_ID)
    if channel:
        embed = discord.Embed(
            title="📥 Biri Aramıza Katıldı!",
            description=f"{member.mention} sunucumuza hoş geldin! Seninle birlikte **{len(member.guild.members)}** kişi olduk. 🎉", 
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        if 'BANNER_URL' in globals() and BANNER_URL.startswith("http") and not BANNER_URL.endswith("..."): 
            embed.set_image(url=BANNER_URL)
        await channel.send(content=f"Hoş geldin {member.mention}!", embed=embed)

@bot.event
async def on_member_remove(member):
    channel = member.guild.get_channel(GELEN_GIDEN_KANAL_ID)
    if channel:
        embed = discord.Embed(
            title="📤 Biri Aramızdan Ayrıldı...",
            description=f"{member.mention} sunucudan ayrıldı. Görüşmek üzere! Geride **{len(member.guild.members)}** kişi kaldık. 😢", 
            color=discord.Color.red()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        if 'BANNER_URL' in globals() and BANNER_URL.startswith("http") and not BANNER_URL.endswith("..."): 
            embed.set_image(url=BANNER_URL)
        await channel.send(content=f"**{member.name}** sunucudan ayrıldı.", embed=embed)


@tasks.loop(seconds=30)
async def keep_alive_loop():
    try:
        req = urllib.request.Request("http://localhost:8080/ping", method="GET")
        with urllib.request.urlopen(req, timeout=5) as r: pass
    except: pass

@bot.event
async def on_ready():
    print(f"Bot sorunsuzca başlatıldı: {bot.user}")
    
    bot.add_view(PanelAnaView())
    bot.add_view(RolBasvuruView())
    bot.add_view(TicketIciAksiyonView())
    
    try:
        for guild in bot.guilds: 
            await bot.tree.sync(guild=guild)
        print("Tüm sistem senkronize edildi!")
    except Exception as e: 
        print(e)
    if not keep_alive_loop.is_running(): 
        keep_alive_loop.start()

TOKEN = os.environ.get('DISCORD_TOKEN', '')
if TOKEN: 
    bot.run(TOKEN, reconnect=True)
