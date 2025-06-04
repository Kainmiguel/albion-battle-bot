import os
import discord
from discord.ext import commands
from bs4 import BeautifulSoup
import requests
from flask import Flask
import threading
import logging

# Configurações
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_NAME = "Os Viriatos"
channel_id_str = os.getenv("DISCORD_CHANNEL_ID")
if not channel_id_str:
    print("[AVISO] Variável DISCORD_CHANNEL_ID não definida. Usando valor padrão de teste.")
    channel_id_str = "1364385962590867483"  # Valor real informado pelo utilizador
CHANNEL_ID = int(channel_id_str)
MIN_MEMBERS = 5

# Intents e bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Flask app para Railway
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot ativo!"

# Web scraping AlbionBattles

def get_latest_battle_link(min_members=MIN_MEMBERS):
    url = "https://eu.albionbattles.com/?search=Os+Viriatos"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        battle_links = soup.select("a[href^='/battles/']")

        seen = set()
        for link_tag in battle_links:
            href = link_tag['href']
            if href in seen:
                continue
            seen.add(href)

            battle_url = f"https://eu.albionbattles.com{href}"
            battle_page = requests.get(battle_url, headers=headers, timeout=10)
            battle_soup = BeautifulSoup(battle_page.text, "html.parser")

            guilds = battle_soup.select("div.flex.items-center.space-x-2 span.font-semibold")
            counts = battle_soup.select("div.flex.items-center.space-x-2 span.text-sm.text-muted")

            for g, c in zip(guilds, counts):
                guild = g.text.strip().lower()
                count_text = c.text.strip().split()[0]
                try:
                    count = int(count_text)
                except ValueError:
                    continue
                if guild == GUILD_NAME.lower() and count >= min_members:
                    return battle_url
        return None
    except Exception as e:
        print("[ERRO] Falha ao verificar batalhas:", e)
        return None

# Nomeações semanais

def buscar_top_jogador(tipo):
    endpoint = {
        "pvp": "https://www.tools4albion.com/api/top/week/pvp",
        "pve": "https://www.tools4albion.com/api/top/week/pve",
        "coleta": "https://www.tools4albion.com/api/top/week/gathering"
    }.get(tipo)
    try:
        res = requests.get(endpoint, timeout=10)
        if res.status_code == 200:
            data = res.json()
            return data[0]["name"] if data else None
        return None
    except Exception as e:
        print(f"[ERRO] Nomeações - {tipo}:", e)
        return None

@bot.command(name="nomeacoes")
async def nomeacoes(ctx):
    await ctx.send("📜 A recolher dados das nomeações gloriosas da semana...")

    pvp = buscar_top_jogador("pvp")
    pve = buscar_top_jogador("pve")
    coleta = buscar_top_jogador("coleta")

    guild = discord.utils.get(bot.guilds, name=GUILD_NAME)

    def menciona(nome):
        membro = discord.utils.get(guild.members, name=nome)
        return membro.mention if membro else f"**{nome}**"

    msg = "🏆 **NOMEAÇÕES DA SEMANA - OS VIRIATOS** 🏆\n\n"
    msg += f"🩸 PvP Mais Sangrento: {menciona(pvp) if pvp else 'Não encontrado'}\n"
    msg += f"⚔️ PvE Mais Incansável: {menciona(pve) if pve else 'Não encontrado'}\n"
    msg += f"⛏️ Coletor Supremo: {menciona(coleta) if coleta else 'Não encontrado'}\n\n"
    msg += "🔥 Honra o passado, constrói o futuro!"

    canal = bot.get_channel(CHANNEL_ID)
    if canal:
        await canal.send(msg)
    else:
        await ctx.send("[ERRO] Canal não encontrado.")

# Comando Discord
@bot.command(name="forcarbatalha")
async def forcar_batalha(ctx):
    await ctx.send("🔍 A verificar batalha fixa no AlbionBB...")
    link = get_latest_battle_link()
    if link:
        await ctx.send(f"🏴 NOVA BATALHA DE {GUILD_NAME.upper()}\n👉 Depositem o loot na tab da guild\n📺 Postem as vossas VODS\n✍️ A vossa presença foi anotada\n{link}")
    else:
        await ctx.send(f"❌ A guilda {GUILD_NAME} não teve {MIN_MEMBERS}+ membros nas últimas batalhas.")

# Inicialização
@bot.event
async def on_ready():
    print(f"{bot.user} está online com scraping AlbionBB ativo! ⚔️")

def start_bot():
    try:
        print("🚀 Bot iniciado com AlbionBB scraping.")
        bot.run(TOKEN)
    except Exception as e:
        print("[ERRO] Falha ao iniciar o bot:", e)

if __name__ == "__main__":
    try:
        bot_thread = threading.Thread(target=start_bot)
        bot_thread.daemon = True
        bot_thread.start()

        print("🌐 Iniciando servidor Flask como processo principal.")
        app.run(host="0.0.0.0", port=8080)
    except KeyboardInterrupt:
        print("[INFO] Encerrado manualmente.")
    except Exception as e:
        print("[ERRO] Exceção no processo principal:", e)
