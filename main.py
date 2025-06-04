import os
import discord
from discord.ext import commands
import requests
from flask import Flask
import threading

# Configurações
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_NAME = "Os Viriatos"
channel_id_str = os.getenv("DISCORD_CHANNEL_ID")
if not channel_id_str:
    print("[AVISO] Variável DISCORD_CHANNEL_ID não definida. Usando valor padrão de teste.")
    channel_id_str = "1364385962590867483"
CHANNEL_ID = int(channel_id_str)

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

# Inicialização
@bot.event
async def on_ready():
    print(f"{bot.user} está online com nomeações ativadas! 🏅")

def start_bot():
    try:
        print("🚀 Bot iniciado com nomeações semanais.")
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
