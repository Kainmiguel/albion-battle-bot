import os
import discord
from discord.ext import commands
import requests
from flask import Flask
import threading

# Configurações
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_NAME = "Os Viriatos"
# ID fixo atualizado
CHANNEL_ID = 1379495247175876819

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

# Nomeações semanais

def buscar_top_jogador(tipo):
    endpoint = {
        "pvp": "https://www.tools4albion.com/api/top/week/pvp",
        "pve": "https://www.tools4albion.com/api/top
