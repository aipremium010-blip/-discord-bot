import discord
import os
from discord import app_commands
from discord.ui import Select, Modal, TextInput, View
from discord.ext import commands
from threading import Thread
from flask import Flask

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
bot = commands.Bot(command_prefix="!", intents=intents)

# === TICKET (DESTEK) SİSTEMİ MODAL VE VİEW'LERİ ===
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

# === GÜNCELLENMİŞ YETKİLİ BAŞVURU SİSTEMİ ===
class YetkiliBasvuruModal(Modal, title="MTTS Yetkili Başvuru Formu"):
    ad_soyad = TextInput(label="Adınız Soyadınız", placeholder="Örn: Ahmet Yılmaz", required=True)
    gorev = TextInput(label="İstediğiniz Görev", placeholder="Örn: Moderatör", required=True)
    aktiflik = TextInput(label="Haftalık Aktiflik Süreniz", placeholder="Örn: Haftada 20 saat", required=True)
    deneyim = TextInput(label="Daha Önce Yetkili Oldunuz mu?", placeholder="Deneyimlerinizi kısaca yazın", style=discord.TextStyle.paragraph, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message("✅ Başvurunuz MTTS yönetim ekibine başarıyla iletildi!", ephemeral=True)

class YetkiliBasvuruView(View):
    def __init__(self): super().__init__(timeout=None)
    
    @discord.ui.button(label="Yetkili Başvurusu İçin Tıkla", style=discord.ButtonStyle.success, emoji="📝", custom_id="mtts_basvuru_btn")
    async def basvuru_btn(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.send_modal(YetkiliBasvuruModal())

# === GÜNCELLENMİŞ PAKET DROPDOWN (MTTS REKLAM PAKETLERİ) ===
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
                "**1. DEMİR PAKET (100 TL)**\n• 1 Everyone + 3 Gün Oda\n\n"
                "**2. ALTIN PAKET (200 TL)**\n• 1 Everyone + 5 Gün Oda + Greet\n\n"
                "**3. ELMAS PAKET (250 TL)**\n• 1 Everyone + 1 Here + 7 Gün Oda + Greet\n\n"
                "**4. NETHERİT PAKET (400 TL)**\n• 2 Everyone + 14 Gün Oda + Greet"
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

# === DİĞER ESKİ ROL/PANEL YAPILARI (UYUMLULUK İÇİN KALICI YAPI) ===
class RolBasvuruView(View):
    def __init__(self): super().__init__(timeout=None)

# === SLASH KOMUTLARI ===
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
async def slash_yetkili_paneli(interaction: discord.Interaction):
    embed = discord.Embed(title="MTTS Yetkili Alımları", description="Yetkili olmak için aşağıdaki butona tıklayın.", color=discord.Color.green())
    await interaction.channel.send(embed=embed, view=YetkiliBasvuruView())
    await interaction.response.send_message("Yetkili paneli kuruldu.", ephemeral=True)

@bot.tree.command(name="sil", description="Belirtilen miktarda mesajı siler.")
@app_commands.checks.has_permissions(administrator=True)
async def slash_sil(interaction: discord.Interaction, miktar: int):
    await interaction.response.defer(ephemeral=True)
    if miktar < 1:
        await interaction.followup.send("❌ En az 1 mesaj silinebilir.", ephemeral=True)
        return
    silinen = await interaction.channel.purge(limit=miktar)
    await interaction.followup.send(f"✅ {len(silinen)} adet mesaj başarıyla silindi.", ephemeral=True)

# === BOT BAŞLAMA VE VIEW KAYITLARI ===
@bot.event
async def on_ready():
    bot.add_view(PanelAnaView())
    bot.add_view(TicketKapatView())
    bot.add_view(PaketPanelView())
    bot.add_view(YetkiliBasvuruView())
    bot.add_view(RolBasvuruView())
    await bot.tree.sync()
    print("--- MTTS Sistemi Başarıyla Başlatıldı ---")

# Web sunucusunu ve botu çalıştırıyoruz
keep_alive()
bot.run(os.environ.get("DISCORD_TOKEN"))
