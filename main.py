import discord
import os
from discord import app_commands
from discord.ui import Select, Modal, TextInput, View
from discord.ext import commands
from threading import Thread
from flask import Flask

# === AYARLAR VE KANAL ID'LERİ ===
BAŞVURU_LOG_KANAL_ID = 1524879141793435689

# Sunucundaki Unvan Rol ID'lerini buraya girmen gerekir (Hata vermemesi için şu an örnek ID'ler yazılıdır)
ROL_SUNUCU_SAHIBI = 123456789012345678
ROL_KLAN_SAHIBI = 123456789012345678
ROL_HOSTING_SAHIBI = 123456789012345678
ROL_ICERIK_URETICISI = 123456789012345678

# === RENDER PORT HATASINI ÇÖZMEK İÇİN KEEPALIVE SİSTEMİ ===
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
intents.members = True # Rol verme ve DM işlemleri için gerekli
bot = commands.Bot(command_prefix="!", intents=intents)

# === TICKET SİSTEMİ ===
class TicketKapatView(View):
    def __init__(self):
        super().__init__(timeout=None)
        
    @discord.ui.button(label="Talebi Kapat", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="ticket_kapat_btn")
    async def ticket_kapat(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.defer()
        await interaction.channel.send("🔒 Bu destek talebi 5 saniye içinde kapatılıyor...")
        await discord.utils.sleep_until(discord.utils.utcnow() + discord.utils.datetime.timedelta(seconds=5))
        await interaction.channel.delete()

class PanelAnaView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Destek Talebi Aç", style=discord.ButtonStyle.primary, emoji="📩", custom_id="ticket_ac_btn")
    async def ticket_ac(self, interaction: discord.Interaction, button: discord.Button):
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

        ticket_channel = await guild.create_text_channel(
            name=f"destek-{member.name}",
            overwrites=overwrites,
            topic=f"{member.id}"
        )
        
        embed = discord.Embed(
            title="📥 MTTS DESTEK SİSTEMİ",
            description=f"Merhaba {member.mention}, destek ekibimiz en kısa sürede sizinle ilgilenecektir.\nTalebi kapatmak için aşağıdaki butona tıklayabilirsiniz.",
            color=discord.Color.blue()
        )
        await ticket_channel.send(embed=embed, view=TicketKapatView())
        await interaction.followup.send(f"✅ Destek talebiniz oluşturuldu: {ticket_channel.mention}", ephemeral=True)

# === BAŞVURU DEĞERLENDİRME BUTONLARI ===
class BasvuruIncelemeView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Onayla", style=discord.ButtonStyle.success, emoji="✅", custom_id="basvuru_onayla_btn")
    async def onayla(self, interaction: discord.Interaction, button: discord.Button):
        embed = interaction.message.embeds[0]
        user_id = int(embed.footer.text.split(" ID: ")[1]) if embed.footer and "ID: " in embed.footer.text else None
        
        embed.color = discord.Color.green()
        embed.title = "✅ YETKİLİ BAŞVURUSU ONAYLANDI"
        embed.set_footer(text=f"Onaylayan Yetkili: {interaction.user.name}")
        
        for item in self.children:
            item.disabled = True
            
        await interaction.response.edit_message(embed=embed, view=self)

        if user_id:
            try:
                user = await interaction.guild.fetch_member(user_id)
                if user:
                    dm_embed = discord.Embed(
                        title="🎉 Tebrikler, Başvurunuz Onaylandı!",
                        description=f"Merhaba {user.mention},\n\n**MTTS** sunucumuz için yaptığınız yetkili başvurusu yönetim ekibimiz tarafından **olumlu** sonuçlandırılmıştır. En kısa sürede yetkiniz tanımlanacaktır. Aramıza hoş geldiniz!",
                        color=discord.Color.green()
                    )
                    await user.send(embed=dm_embed)
            except Exception:
                pass

    @discord.ui.button(label="Reddet", style=discord.ButtonStyle.danger, emoji="❌", custom_id="basvuru_reddet_btn")
    async def reddet(self, interaction: discord.Interaction, button: discord.Button):
        embed = interaction.message.embeds[0]
        user_id = int(embed.footer.text.split(" ID: ")[1]) if embed.footer and "ID: " in embed.footer.text else None
        
        embed.color = discord.Color.red()
        embed.title = "❌ YETKİLİ BAŞVURUSU REDDEDİLDİ"
        embed.set_footer(text=f"Reddeden Yetkili: {interaction.user.name}")
        
        for item in self.children:
            item.disabled = True
            
        await interaction.response.edit_message(embed=embed, view=self)

        if user_id:
            try:
                user = await interaction.guild.fetch_member(user_id)
                if user:
                    dm_embed = discord.Embed(
                        title="Maalesef, Başvurunuz Reddedildi",
                        description=f"Merhaba {user.mention},\n\n**MTTS** sunucumuz için yaptığınız yetkili başvurusu yönetim ekibimiz tarafından maalesef **uygun görülmemiştir**.",
                        color=discord.Color.red()
                    )
                    await user.send(embed=dm_embed)
            except Exception:
                pass

# === YETKİLİ BAŞVURU FORMU ===
class YetkiliBasvuruModal(Modal, title="MTTS Yetkili Başvuru Formu"):
    ad = TextInput(label="Adınız", placeholder="Örn: Ahmet", required=True)
    gorev = TextInput(label="İstediğiniz Görev", placeholder="Örn: Moderatör", required=True)
    aktiflik = TextInput(label="Haftalık Aktiflik Süreniz", placeholder="Örn: Haftada 20 saat", required=True)
    deneyim = TextInput(label="Daha Önce Yetkili Oldunuz mu?", placeholder="Deneyimlerinizi kısaca yazın", style=discord.TextStyle.paragraph, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message("✅ Başvurunuz MTTS yönetim ekibine başarıyla iletildi!", ephemeral=True)
        
        log_channel = interaction.guild.get_channel(BAŞVURU_LOG_KANAL_ID)
        if log_channel:
            embed = discord.Embed(
                title="📝 YENİ YETKİLİ BAŞVURUSU GELDİ",
                color=discord.Color.orange()
            )
            embed.add_field(name="👤 Başvuran Kullanıcı:", value=f"{interaction.user.mention} ({interaction.user.name})", inline=False)
            embed.add_field(name="✍️ İsim:", value=self.ad.value, inline=True)
            embed.add_field(name="🛡️ İstediği Görev:", value=self.gorev.value, inline=True)
            embed.add_field(name="⏰ Aktiflik Süresi:", value=self.aktiflik.value, inline=False)
            embed.add_field(name="📖 Deneyimleri:", value=self.deneyim.value, inline=False)
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            embed.set_footer(text=f"Kullanıcı ID: {interaction.user.id}")
            
            await log_channel.send(embed=embed, view=BasvuruIncelemeView())

class YetkiliBasvuruView(View):
    def __init__(self): super().__init__(timeout=None)
    
    @discord.ui.button(label="Başvuru Formunu Aç", style=discord.ButtonStyle.success, emoji="📝", custom_id="mtts_basvuru_btn")
    async def basvuru_btn(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.send_modal(YetkiliBasvuruModal())

# === FOTOĞRAFTAKİ HATA VEREN UNVAN PANELİ BUTONLARI VE CODES ===
class RolBasvuruView(View):
    def __init__(self):
        super().__init__(timeout=None)

    async def rol_ver_kaldir(self, interaction: discord.Interaction, role_id: int, rol_ismi: str):
        await interaction.response.defer(ephemeral=True)
        role = interaction.guild.get_role(role_id)
        if not role:
            await interaction.followup.send(f"❌ `{rol_ismi}` rolü sunucuda bulunamadı. Lütfen bot kodundaki ID ayarlarını yapın.", ephemeral=True)
            return
        
        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.followup.send(f"🗑️ Başarıyla `{rol_ismi}` rolü üzerinizden alındı.", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.followup.send(f"✅ Başarıyla `{rol_ismi}` rolü size tanımlandı.", ephemeral=True)

    @discord.ui.button(label="Sunucu Sahibi", style=discord.ButtonStyle.primary, emoji="👑", custom_id="unvan_sunucu_sahibi")
    async def sunucu_sahibi(self, interaction: discord.Interaction, button: discord.Button):
        await self.rol_ver_kaldir(interaction, ROL_SUNUCU_SAHIBI, "Sunucu Sahibi")

    @discord.ui.button(label="Klan Sahibi", style=discord.ButtonStyle.primary, emoji="⚔️", custom_id="unvan_klan_sahibi")
    async def klan_sahibi(self, interaction: discord.Interaction, button: discord.Button):
        await self.rol_ver_kaldir(interaction, ROL_KLAN_SAHIBI, "Klan Sahibi")

    @discord.ui.button(label="Hosting Sahibi", style=discord.ButtonStyle.primary, emoji="💻", custom_id="unvan_hosting_sahibi")
    async def hosting_sahibi(self, interaction: discord.Interaction, button: discord.Button):
        await self.rol_ver_kaldir(interaction, ROL_HOSTING_SAHIBI, "Hosting Sahibi")

    @discord.ui.button(label="İçerik Üreticisi", style=discord.ButtonStyle.primary, emoji="🎬", custom_id="unvan_icerik_ureticisi")
    async def icerik_ureticisi(self, interaction: discord.Interaction, button: discord.Button):
        await self.rol_ver_kaldir(interaction, ROL_ICERIK_URETICISI, "İçerik Üreticisi")

# === REKLAM DROPDOWN SİSTEMİ ===
class PaketDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Ping Hizmetleri", value="ping_hizmet", emoji="📢"),
            discord.SelectOption(label="MTTS Reklam Paketleri", value="mtts_reklam", emoji="💵")
        ]
        super().__init__(placeholder="🔻 Paket Seçin:", min_values=1, max_values=1, options=options, custom_id="paket_ana_dropdown")

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "mtts_reklam":
            embed = discord.Embed(title="💎 MTTS REKLAM PAKETLERİ", color=discord.Color.gold())
            embed.description = (
                "**1. DEMİR PAKET (100 TL)**\n• 1 Everyone + 3 Gün Oda\n• *Çekiliş Sizden*\n\n"
                "**2. ALTIN PAKET (200 TL)**\n• 1 Everyone + 5 Gün Oda + Greet\n• *Çekiliş Bizden*\n\n"
                "**3. ELMAS PAKET (250 TL)**\n• 1 Everyone + 1 Here + 7 Gün Oda + Greet\n• *Çekiliş Bizden*\n\n"
                "**4. NETHERİT PAKET (400 TL)**\n• 2 Everyone + 14 Gün Oda + Greet\n• *Çekiliş Bizden*"
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        elif self.values[0] == "ping_hizmet":
            embed = discord.Embed(title="📢 PING HİZMETLERİ", color=discord.Color.from_rgb(230, 126, 34))
            embed.description = "🔵 **Anlık `@everyone` Ping:** `80 TL`\n🟡 **Anlık `@here` Ping:** `50 TL`"
            await interaction.response.send_message(embed=embed, ephemeral=True)

class PaketPanelView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(PaketDropdown())

# === İLAN VERME SİSTEMİ MODALI ===
class IlanVerModal(Modal, title="Yeni İlan Oluştur"):
    urun = TextInput(label="Ürün Adı", placeholder="Örn: Discord Nitro", required=True)
    fiyat = TextInput(label="Fiyat (TL)", placeholder="Örn: 30", required=True)
    aciklama = TextInput(label="Açıklama / İletişim Notu", placeholder="Örn: Discord Nitro için DM atın", style=discord.TextStyle.paragraph, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        embed = discord.Embed(title="🛒 Yeni İlan", color=discord.Color.orange())
        embed.add_field(name="👤 İlan Sahibi", value=interaction.user.mention, inline=False)
        embed.add_field(name="📦 Ürün", value=self.urun.value, inline=True)
        embed.add_field(name="💰 Fiyat", value=f"{self.fiyat.value} TL", inline=True)
        embed.add_field(name="📝 Açıklama", value=self.aciklama.value, inline=False)
        embed.set_footer(text=f"İlan Tarihi: {discord.utils.utcnow().strftime('%d/%m/%Y')}")
        
        # Gönderilen ilana onay/red reaksiyon emojileri ekleyelim (Fotoğraftaki gibi)
        mesaj = await interaction.channel.send(embed=embed)
        await mesaj.add_reaction("✅")
        await mesaj.add_reaction("❌")
        await interaction.followup.send("✅ İlanınız başarıyla yayınlandı!", ephemeral=True)

# === GÜNCELLENMİŞ SLASH KOMUTLARI ===

@bot.tree.command(name="sil", description="Belirtilen miktarda mesajı siler.")
@app_commands.checks.has_permissions(administrator=True)
async def slash_sil(interaction: discord.Interaction, miktar: int):
    await interaction.response.defer(ephemeral=True)
    if miktar < 1:
        await interaction.followup.send("❌ En az 1 mesaj silinebilir.", ephemeral=True)
        return
    silinen = await interaction.channel.purge(limit=miktar)
    await interaction.followup.send(f"✅ {len(silinen)} adet mesaj başarıyla silindi.", ephemeral=True)

@bot.tree.command(name="lock", description="Bulunduğunuz kanalı mesaj gönderimine kapatır.")
@app_commands.checks.has_permissions(administrator=True)
async def slash_lock(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
    overwrite.send_messages = False
    await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
    await interaction.channel.send("🔒 Bu kanal metin gönderimine **kapatılmıştır**.")
    await interaction.followup.send("Kanal kilitlendi.", ephemeral=True)

@bot.tree.command(name="unlock", description="Kilitli kanalı tekrar mesaj gönderimine açar.")
@app_commands.checks.has_permissions(administrator=True)
async def slash_unlock(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
    overwrite.send_messages = True
    await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
    await interaction.channel.send("🔓 Bu kanal metin gönderimine tekrar **açılmıştır**.")
    await interaction.followup.send("Kanal kilidi açıldı.", ephemeral=True)

@bot.tree.command(name="mesaj", description="Bot adına kanala şık bir embed duyuru mesajı gönderir.")
@app_commands.checks.has_permissions(administrator=True)
async def slash_mesaj(interaction: discord.Interaction, baslik: str, icerik: str):
    embed = discord.Embed(title=baslik, description=icerik, color=discord.Color.blue())
    if interaction.guild.icon:
        embed.set_thumbnail(url=interaction.guild.icon.url)
    await interaction.channel.send(embed=embed)
    await interaction.response.send_message("Embed mesajı gönderildi.", ephemeral=True)

@bot.tree.command(name="ilan-ver", description="Sunucuda yeni bir ticaret veya takas ilanı yayınlar.")
async def slash_ilan_ver(interaction: discord.Interaction):
    await interaction.response.send_modal(IlanVerModal())

@bot.tree.command(name="unvan-paneli", description="Unvan Doğrulama Başvuru panelini kurar.")
@app_commands.checks.has_permissions(administrator=True)
async def slash_unvan_paneli(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Unvan Doğrulama Başvuruları",
        description="Sunucu sahibi, klan lideri, hosting firması veya içerik üreticisi unvanlarına sahipseniz rollerinizi teslim almak için aşağıdaki butonlara tıklayın.",
        color=discord.Color.dark_magenta()
    )
    if interaction.guild.icon:
        embed.set_thumbnail(url=interaction.guild.icon.url)
    await interaction.channel.send(embed=embed, view=RolBasvuruView())
    await interaction.response.send_message("Unvan paneli kuruldu.", ephemeral=True)

@bot.tree.command(name="destek-panel", description="MTTS Destek panelini kurar.")
@app_commands.checks.has_permissions(administrator=True)
async def slash_destek_panel(interaction: discord.Interaction):
    embed = discord.Embed(title="📥 MTTS DESTEK SİSTEMİ", description="Destek talebi oluşturmak için aşağıdaki butona tıklayabilirsiniz.", color=discord.Color.blue())
    await interaction.channel.send(embed=embed, view=PanelAnaView())
    await interaction.response.send_message("Destek paneli kuruldu.", ephemeral=True)

@bot.tree.command(name="paketler", description="MTTS Hizmet Paketleri paneli")
async def slash_paketler(interaction: discord.Interaction):
    embed = discord.Embed(title="MTTS Hizmetleri", description="Aşağıdaki menüden paketleri inceleyebilirsiniz.", color=discord.Color.blue())
    await interaction.channel.send(embed=embed, view=PaketPanelView())
    await interaction.response.send_message("Hizmet paneli kuruldu.", ephemeral=True)

@bot.tree.command(name="yetkili-paneli", description="MTTS Yetkili Paneli")
@app_commands.checks.has_permissions(administrator=True)
async def slash_yetkili_paneli(interaction: discord.Interaction):
    embed = discord.Embed(
        title="✨ MTTS YETKİLİ ALIMLARI BAŞLADI! ✨",
        description=(
            "**Minecraft Türkiye Topluluk Sunucusu (MTTS)** yönetim ekibine katılarak topluluğumuzu büyütmemize yardımcı olmak ister misin?\n\n"
            "🛡️ **Yönetim Ekibinde Seni Neler Bekliyor?**\n"
            "• Sunucu içi düzeni ve huzuru sağlama,\n"
            "• Üyelerimize destek kanallarında yardımcı olma,\n"
            "• Adil, eğlenceli ve aktif bir ekibin parçası olma şansı!\n\n"
            "⚠️ **Başvuru Şartları ve Kurallar:**\n"
            "• Formu tamamen **doğru ve dürüst** bilgilerle doldurmalısın.\n"
            "• Başvurun onaylandığında ya da reddedildiğinde bot sana **Özel Mesaj (DM)** yoluyla bilgilendirme yapacaktır.\n\n"
            "🌟 Ekibimize katılmak için aşağıdaki yeşil butona tıklayarak formu doldurabilirsin!"
        ),
        color=discord.Color.from_rgb(46, 204, 113)
    )
    if interaction.guild.icon:
        embed.set_author(name="MTTS Yönetim Ekibi Alımları", icon_url=interaction.guild.icon.url)
        embed.set_image(url=interaction.guild.icon.url)
    
    await interaction.channel.send(embed=embed, view=YetkiliBasvuruView())
    await interaction.response.send_message("Yetkili paneli başarıyla güncellendi ve kuruldu.", ephemeral=True)

# === BOT BAŞLAMA VE VIEW KAYITLARI ===
@bot.event
async def on_ready():
    bot.add_view(PanelAnaView())
    bot.add_view(TicketKapatView())
    bot.add_view(PaketPanelView())
    bot.add_view(YetkiliBasvuruView())
    bot.add_view(RolBasvuruView()) # Fotoğraftaki buton etkileşim hatasını çözen kalıcı view kaydı
    bot.add_view(BasvuruIncelemeView())
    await bot.tree.sync()
    print("--- MTTS Sistemi Başarıyla Başlatıldı ---")

keep_alive()
bot.run(os.environ.get("DISCORD_TOKEN"))
