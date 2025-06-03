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
    await ctx.send("🔍 A verificar batalha fixa no AlbionBB...")

    battle_url = "https://europe.albionbb.com/battles/198916189"
    res = requests.get(battle_url)
    if res.status_code != 200:
        await ctx.send("❌ Erro ao aceder à página da batalha.")
        return

    soup = BeautifulSoup(res.text, "html.parser")
    tables = soup.find_all("table")
    if not tables:
        await ctx.send("❌ Nenhuma tabela encontrada na página da batalha.")
        return

    encontrou = False
    for table in tables:
        headers = [th.get_text(strip=True).lower() for th in table.find_all("th")]
        if "guild" in headers and "players" in headers:
            rows = table.find_all("tr")[1:]
            for row in rows:
                cells = row.find_all("td")
                if len(cells) < 2:
                    continue
                guild_name_raw = cells[0].get_text(separator=" ", strip=True)
                players_text = cells[1].get_text(strip=True)

                # 💬 Debug: imprimir nome da guilda
                guild_name = re.sub(r"\s+", " ", guild_name_raw).lower()
                print(f"[DEBUG] Guilda encontrada: '{guild_name}' com {players_text} jogadores")

                try:
                    players = int(players_text)
                except ValueError:
                    continue

                if "os viriatos" in guild_name and players >= 10:
                    encontrou = True
                    break

    if encontrou:
        timestamp_elem = soup.find("h1")
        timestamp = timestamp_elem.get_text(strip=True) if timestamp_elem else "Data desconhecida"

        embed = discord.Embed(
            title="🏴 NOVA BATALHA DE Os Viriatos",
            description=f"👉 Depositem o loot
