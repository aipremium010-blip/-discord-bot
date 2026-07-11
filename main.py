import discord
from discord import app_commands
from discord.ui import Select, Modal, TextInput, View
from discord.ext import commands

# BOT AYARLARI
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# === MODALLAR (Başvuru) ===
class YetkiliBasvuruModal(Modal, title="MTTS Yetkili Başvuru Formu"):
    ad_soyad = TextInput(label="Adınız Soyadınız", placeholder="Örn: Ahmet Yılmaz", required=True)
    gorev = TextInput(label="İstediğiniz Görev", placeholder="Örn: Moderatör", required=True)
    aktiflik = TextInput(label="Haftalık Aktiflik Süreniz", placeholder="Örn: Haftada 20 saat", required=True)
    deneyim = TextInput(label="Daha Önce Yetkili Oldunuz mu?", placeholder="Deneyimlerinizi kısaca yazın", style=discord.TextStyle.paragraph, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message("✅ Başvurunuz MTTS yönetim ekibine başarıyla iletildi!", ephemeral=True)

# === VIEWLER (Butonlar ve Dropdownlar) ===
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

class YetkiliBasvuruView(View):
    def __init__(self): super().__init__(timeout=None)
    
    @discord.ui.button(label="Yetkili Başvurusu İçin Tıkla", style=discord.ButtonStyle.success, emoji="📝", custom_id="mtts_basvuru_btn")
    async def basvuru_btn(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.send_modal(YetkiliBasvuruModal())

# === KOMUTLAR ===
@bot.tree.command(name="paketler", description="MTTS Hizmet Paketleri paneli")
async def slash_paketler(interaction: discord.Interaction):
    embed = discord.Embed(title="MTTS Hizmetleri", description="Aşağıdaki menüden paketleri inceleyebilirsiniz.", color=discord.Color.blue())
    await interaction.channel.send(embed=embed, view=PaketPanelView())
    await interaction.response.send_message("Panel başarıyla kuruldu.", ephemeral=True)

@bot.tree.command(name="yetkili-paneli", description="MTTS Yetkili Paneli")
async def slash_yetkili_paneli(interaction: discord.Interaction):
    embed = discord.Embed(title="MTTS Yetkili Alımları", description="Yetkili olmak için aşağıdaki butona tıklayın.", color=discord.Color.green())
    await interaction.channel.send(embed=embed, view=YetkiliBasvuruView())
    await interaction.response.send_message("MTTS yetkili paneli başarıyla kuruldu.", ephemeral=True)

# === BAŞLATMA ===
@bot.event
async def on_ready():
    bot.add_view(PaketPanelView())
    bot.add_view(YetkiliBasvuruView())
    await bot.tree.sync()
    print("--- MTTS Bot başarıyla başlatıldı ve senkronize edildi! ---")

bot.run("TOKEN_BURAYA")
