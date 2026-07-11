import discord
import os
import random
import asyncio
from discord import app_commands
from discord.ui import Select, Modal, TextInput, View
from discord.ext import commands
from threading import Thread
from flask import Flask

# === AYARLAR VE KANAL ID'LERİ ===
BAŞVURU_LOG_KANAL_ID = 1524879141793435689
GIRIS_CIKIS_KANAL_ID = 123456789012345678  # Giriş-Çıkış log kanal ID'si

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

# === GİRİŞ VE ÇIKIŞ SİSTEMİ ===
@bot.event
async def on_member_join(member):
    channel = member.guild.get_channel(GIRIS_CIKIS_KANAL_ID)
    if channel:
        embed = discord.Embed(
            description=f"{member.mention} aramıza hoş geldin! **{member.guild.member_count}** kişiyiz.",
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

# === 2. PAKETLER SİSTEMİ (REKLAM PAKETLERİ) ===
class PaketDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Bronz Paket", value="bronz", emoji="🥉"),
            discord.SelectOption(label="Gümüş Paket", value="gumus", emoji="🥈"),
            discord.SelectOption(label="Altın Paket", value="altin", emoji="🥇")
        ]
        super().__init__(placeholder="Detaylarını görmek istediğiniz paketi seçin", options=options, custom_id="reklam_paket_dropdown")

    async def callback(self, interaction: discord.Interaction):
        secilen = self.values[0]
        embed = discord.Embed(color=discord.Color.blue())
        
        if secilen == "bronz":
            embed.title = "🥉 Bronz Reklam Paketi"
            embed.description = "• 1 Adet @everyone Etiketli Duyuru\n• 24 Saat Sabit Kanal\n• **Çekiliş sizden** (Ödül sunucu tarafından karşılanır)"
        elif secilen == "gumus":
            embed.title = "🥈 Gümüş Reklam Paketi"
            embed.description = "• 2 Adet @everyone Etiketli Duyuru\n• 48 Saat Sabit Kanal\n• Çekiliş ve Katılım Yönetimi"
        elif secilen == "altin":
            embed.title = "🥇 Altın Reklam Paketi"
            embed.description = "• 3 Adet @everyone Etiketli Duyuru\n• 1 Hafta Sabit Kanal\n• Özel Sponsor Rolü & Katılım Desteği"
            
        await interaction.response.send_message(embed=embed, ephemeral=True)

class PaketPanelView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(PaketDropdown())

# === 3. YETKİLİ / ROL BAŞVURU SİSTEMLERİ ===
class YetkiliBasvuruIncelemeView(View):
    def __init__(self, basvuran_id: int):
        super().__init__(timeout=None)
        self.basvuran_id = basvuran_id

    @discord.ui.button(label="Onayla", style=discord.ButtonStyle.success, custom_id="yb_onay")
    async def onay(self, interaction: discord.Interaction, button: discord.Button):
        üye = interaction.guild.get_member(self.basvuran_id)
        if üye:
            await interaction.response.send_message(f"✅ {üye.mention} onaylandı.", ephemeral=True)
            await üye.send("🎉 MTTS Yetkili başvurunuz kabul edildi!")

    @discord.ui.button(label="Reddet", style=discord.ButtonStyle.danger, custom_id="yb_red")
    async def reddet(self, interaction: discord.Interaction, button: discord.Button):
        üye = interaction.guild.get_member(self.basvuran_id)
        if üye:
            await interaction.response.send_message(f"❌ {üye.mention} reddedildi.", ephemeral=True)
            await üye.send("Maalesef, MTTS Yetkili başvurunuz olumsuz sonuçlandı.")

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
        self.sunucu_detay = TextInput(label="Sunucu Detay", style=discord.TextStyle.paragraph, required=True)
        self.sunucu_link = TextInput(label="Sunucu Link", placeholder="discord.gg/...", required=True)
        self.add_item(self.ad)
        self.add_item(self.sunucu_adi)
        self.add_item(self.sunucu_detay)
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
            embed.add_field(name="Detay", value=self.sunucu_detay.value, inline=False)
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

# === 4. YENİ EKLENEN SLASH KOMUTLARI (ANKET, ÇEKİLİŞ, LOCK, UNLOCK) ===
@bot.tree.command(name="anket", description="Sunucuda oylama/anket başlatır.")
@app_commands.checks.has_permissions(manage_messages=True)
async def slash_anket(interaction: discord.Interaction, soru: str):
    embed = discord.Embed(title="📊 Yeni Anket / Oylama", description=soru, color=discord.Color.purple())
    embed.set_footer(text=f"Başlatan: {interaction.user.name}")
    
    # Yanıtı gönderip mesaja emojileri basıyoruz
    await interaction.response.send_message("Anket oluşturuluyor...", ephemeral=True)
    msg = await interaction.channel.send(embed=embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")

@bot.tree.command(name="cekilis", description="Hızlı bir çekiliş düzenler.")
@app_commands.checks.has_permissions(manage_messages=True)
async def slash_cekilis(interaction: discord.Interaction, sure_saniye: int, odul: str):
    embed = discord.Embed(title="🎉 ÇEKİLİŞ BAŞLADI! 🎉", description=f"**Ödül:** {odul}\n**Süre:** {sure_saniye} saniye\n\nKatılmak için 🎉 tepkisine tıklayın!", color=discord.Color.gold())
    await interaction.response.send_message("Çekiliş başlatıldı.", ephemeral=True)
    
    msg = await interaction.channel.send(embed=embed)
    await msg.add_reaction("🎉")
    
    await asyncio.sleep(sure_saniye)
    
    # Mesajı yeniden çekip reaksiyon verenleri buluyoruz
    msg = await interaction.channel.fetch_message(msg.id)
    reaction = discord.utils.get(msg.reactions, emoji="🎉")
    users = [user async for user in reaction.users() if not user.bot]
    
    if users:
        kazanan = random.choice(users)
        await interaction.channel.send(f"🎉 Tebrikler {kazanan.mention}! **{odul}** çekilişini kazandın!")
    else:
        await interaction.channel.send("❌ Çekilişe kimse katılmadığı için kazanan belirlenemedi.")

@bot.tree.command(name="destek-panel", description="Açılır Menülü Destek panelini kurar.")
@app_commands.checks.has_permissions(administrator=True)
async def slash_destek_panel(interaction: discord.Interaction):
    embed = discord.Embed(title="📥 Destek Menüsü", description="Aşağıdaki menüden destek talebi açabilirsiniz.", color=discord.Color.green())
    await interaction.channel.send(embed=embed, view=DestekPanelView())
    await interaction.response.send_message("Destek paneli kuruldu.", ephemeral=True)

@bot.tree.command(name="paket-panel", description="Reklam paketleri panelini kurar.")
@app_commands.checks.has_permissions(administrator=True)
async def slash_paket_panel(interaction: discord.Interaction):
    embed = discord.Embed(title="💵 Reklam Paketleri", description="Sunucumuzda reklam vermek için paket detaylarını aşağıdan inceleyebilirsiniz.", color=discord.Color.blue())
    await interaction.channel.send(embed=embed, view=PaketPanelView())
    await interaction.response.send_message("Paket paneli kuruldu.", ephemeral=True)

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

# === BOT ON_READY KAYITLARI ===
@bot.event
async def on_ready():
    bot.add_view(DestekPanelView())
    bot.add_view(DestekKanalIciView())
    bot.add_view(YetkiliBasvuruView())
    bot.add_view(RolBasvuruView())
    bot.add_view(PaketPanelView())
    await bot.tree.sync()
    print("--- Tüm Sistemler (Anket, Çekiliş, Paketler dahil) Eksiksiz Aktif! ---")

keep_alive()
bot.run(os.environ.get("DISCORD_TOKEN"))
