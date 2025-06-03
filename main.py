import discord
from discord.ext import commands
import requests
from bs4 import BeautifulSoup
import os
import re
from flask import Flask
from threading import Thread
import time

# 🔧 Flask para manter Railway ativo
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Bot Viriatos ativo!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# 🤖 Configuração do bot Discord
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"{bot.user} está online com modo DEBUG + Flask ativo! 🛠️")

@bot.event
async def on_message(message):
    print(f"[DEBUG] Mensagem recebida: {message.content} de {message.author}")
    await bot.process_commands(message)

@bot.command(name="forcarbatalha")
async def forcar_batalha(ctx):
    await ctx.send("🔍 A verificar batalhas no AlbionBB com 10+ membros...")

    url = "https://europe.albionbb.com/?search=Os+Viriatos"
    res = requests.get(url)
    if res.status_code != 200:
        await ctx.send("❌ Erro ao aceder ao AlbionBB.")
        return

    soup = BeautifulSoup(res.text, "html.parser")
    battle_links = soup.select("a[href^='/battles/']")

    if not battle_links:
        await ctx.send("❌ Nenhuma batalha encontrada no AlbionBB.")
        return

    for link in battle_links:
        battle_url = "https://europe.albionbb.com" + link["href"]
        battle_res = requests.get(battle_url)
        if battle_res.status_code != 200:
            continue

        battle_soup = BeautifulSoup(battle_res.text, "html.parser")
        guilds_header = battle_soup.find("h2", string="Guilds")
        if not guilds_header:
            continue

        guilds_table = guilds_header.find_next("table")
        if not guilds_table:
            continue

        rows = guilds_table.find_all("tr")[1:]  # Ignora cabeçalho
        for row in rows:
            cells = row.find_all("td")
            if len(cells) < 2:
                continue
            guild_name = cells[0].get_text(strip=True)
            players = int(cells[1].get_text(strip=True))
            if "Os Viriatos" in guild_name and players >= 10:
                timestamp_elem = battle_soup.find("h1")
                timestamp = timestamp_elem.get_text(strip=True) if timestamp_elem else "Data desconhecida"

                embed = discord.Embed(
                    title="🏴 NOVA BATALHA DE Os Viriatos",
                    description=f"👉 Depositem o loot na tab da guild\n📺 Postem as vossas VODS\n✍️ A vossa presença foi anotada\n\n🕒 {timestamp}",
                    url=battle_url,
                    color=0
                )
                embed.set_image(url="https://cdn.discordapp.com/attachments/1366525638621528074/1379488133355147375/albion_zvz.jpeg")
                await ctx.send(embed=embed)
                return

    await ctx.send("❌ Nenhuma batalha com 10+ membros da guilda foi encontrada.")

# 🔄 Ativar servidor Flask
keep_alive()

# 🚀 Iniciar o bot Discord com proteção contra falhas
token = os.getenv("DISCORD_TOKEN")

if not token:
    print("❌ ERRO: Token DISCORD_TOKEN não está definido nas variáveis de ambiente.")
    while True:
        time.sleep(60)
else:
    print("🚀 Token carregado. Iniciando bot...")
    try:
        bot.run(token)
    except Exception as e:
        print("❌ ERRO ao iniciar o bot:", e)
        while True:
            time.sleep(60)
