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
    
    if 'BANNER_URL' in globals() and BANNER_URL.startswith("http") and not BANNER_URL.endswith("..."): 
        embed.set_thumbnail(url=BANNER_URL)

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
