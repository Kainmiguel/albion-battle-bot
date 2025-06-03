import discord
from discord.ext import commands
import requests
from bs4 import BeautifulSoup
import os

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"{bot.user} está online com AlbionBB! ⚔️")

@bot.command(name="forcarbatalha")
async def forcar_batalha(ctx):
    await ctx.send("🔍 A verificar batalhas em AlbionBB...")

    url = "https://europe.albionbb.com/?search=Os+Viriatos"
    res = requests.get(url)
    if res.status_code != 200:
        await ctx.send("❌ Erro ao aceder ao AlbionBB.")
        return

    soup = BeautifulSoup(res.text, "html.parser")
    cards = soup.select("div.card-body")[:3]

    if not cards:
        await ctx.send("❌ Nenhuma batalha encontrada no AlbionBB.")
        return

    for card in cards:
        title_elem = card.select_one("h5")
        link_elem = card.select_one("a[href*='battle']")
        time_elem = card.select_one("small.text-muted")

        if not (title_elem and link_elem):
            continue

        title = title_elem.text.strip()
        link = "https://europe.albionbb.com" + link_elem["href"]
        timestamp = time_elem.text.strip() if time_elem else ""

        embed = discord.Embed(
            title="🏴 NOVA BATALHA DE Os Viriatos",
            description=f"👉 Depositem o loot na tab da guild\n📺 Postem as vossas VODS\n✍️ A vossa presença foi anotada\n\n🕒 {timestamp}",
            url=link,
            color=0
        )
        embed.set_image(url="https://cdn.discordapp.com/attachments/1366525638621528074/1379488133355147375/albion_zvz.jpeg")
        await ctx.send(embed=embed)

bot.run(os.getenv("DISCORD_TOKEN"))
