import discord
from discord.ext import commands, tasks
import requests
from datetime import datetime, timedelta
import os
import pytz
import random

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

GUILD_ID = "sMgQvZkqQy-QdnRZ1GmfFw"
NOMEACOES_CHANNEL_ID = 1379495247175876819

# Alcunhas temáticas automáticas
alcunhas_pvp = ["Viriato Sangrento", "Espada de Lusitânia", "Ceifador do Norte", "Gládio Imortal"]
alcunhas_pve = ["Escudo de Lusitânia", "Guardião da Bravura", "Caçador Sagrado", "Lâmina da Justiça"]
alcunhas_gather = ["Picareta Sagrada", "Martelo da Terra", "Mãos de Ouro", "Coletor dos Montes"]

@bot.event
async def on_ready():
    print(f"BATTLE BOT '{bot.user}' está online ⚔️")
    nomeacoes_task.start()

@bot.command(name="forcarbatalha")
async def forcar_batalha(ctx):
    await ctx.send("🔍 A verificar batalhas recentes...")

    res = requests.get(f"https://gameinfo.albiononline.com/api/gameinfo/guilds/{GUILD_ID}/deaths?limit=50")
    if res.status_code != 200:
        await ctx.send("❌ Erro ao buscar dados da API.")
        return

    deaths = res.json()
    grouped = []
    for death in deaths:
        ts = datetime.strptime(death["TimeStamp"], "%Y-%m-%dT%H:%M:%S")
        found = False
        for group in grouped:
            if abs((ts - group["time"]).total_seconds()) <= 120 and death["Location"] == group["location"]:
                group["deaths"].append(death)
                found = True
                break
        if not found:
            grouped.append({"time": ts, "location": death["Location"], "deaths": [death]})

    for group in grouped:
        guild_players = set()
        for death in group["deaths"]:
            if death["Victim"]["GuildName"] == "Os Viriatos":
                guild_players.add(death["Victim"]["Name"])
            if death["Killer"] and death["Killer"]["GuildName"] == "Os Viriatos":
                guild_players.add(death["Killer"]["Name"])

        if len(guild_players) < 10:
            continue

        embed = discord.Embed(
            title="🏴 NOVA BATALHA DE Os Viriatos",
            description="👉 Depositem o loot na tab da guild\n📺 Postem as vossas VODS\n✍️ A vossa presença foi anotada",
            url="https://europe.albionbb.com/?search=Os+Viriatos",
            color=0
        )
        embed.set_image(url="https://cdn.discordapp.com/attachments/1366525638621528074/1379488133355147375/albion_zvz.jpeg")

        await ctx.send(embed=embed)
        return

    await ctx.send("❌ Nenhuma batalha recente com 10+ membros da guilda encontrada.")

def buscar_fama_jogadores():
    base_url = "https://gameinfo.albiononline.com/api/gameinfo"
    members_url = f"{base_url}/guilds/{GUILD_ID}/members"
    res = requests.get(members_url)
    if res.status_code != 200:
        return None

    members = res.json()
    ranking = []

    for member in members:
        player_id = member.get("Id")
        name = member.get("Name")
        fame_url = f"{base_url}/players/{player_id}/fame"
        fame_res = requests.get(fame_url)
        if fame_res.status_code != 200:
            continue
        fame_data = fame_res.json()
        ranking.append({
            "name": name,
            "pvp": fame_data.get("LifetimePvP", 0),
            "pve": fame_data.get("LifetimePvE", 0),
            "gather": fame_data.get("Gathering", 0)
        })

    if not ranking:
        return None

    top_pvp = max(ranking, key=lambda x: x["pvp"])
    top_pve = max(ranking, key=lambda x: x["pve"])
    top_gather = max(ranking, key=lambda x: x["gather"])

    return {
        "pvp": top_pvp,
        "pve": top_pve,
        "gather": top_gather
    }

@tasks.loop(minutes=60)
async def nomeacoes_task():
    now = datetime.now(pytz.timezone("Europe/Lisbon"))
    if now.weekday() == 6 and now.hour == 21:  # Domingo às 21h (Portugal)
        canal = bot.get_channel(NOMEACOES_CHANNEL_ID)
        if not canal:
            print("❌ Canal de nomeações não encontrado.")
            return

        tops = buscar_fama_jogadores()
        if not tops:
            await canal.send("❌ Não foi possível buscar os dados de fama esta semana.")
            return

        alcunha_pvp = random.choice(alcunhas_pvp)
        alcunha_pve = random.choice(alcunhas_pve)
        alcunha_gather = random.choice(alcunhas_gather)

        msg = (
            "🏛️ **OS VIRIATOS – NOMEAÇÕES DA SEMANA**\n\n"
            f"⚔️ *{alcunha_pvp}* – **{tops['pvp']['name']}**, {tops['pvp']['pvp']:,} fama PvP\n"
            f"🛡️ *{alcunha_pve}* – **{tops['pve']['name']}**, {tops['pve']['pve']:,} fama PvE\n"
            f"⛏️ *{alcunha_gather}* – **{tops['gather']['name']}**, {tops['gather']['gather']:,} fama Coleta\n\n"
            "Honra e glória aos heróis da semana! 🇵🇹"
        )

        await canal.send(msg)

bot.run(os.getenv("DISCORD_TOKEN"))
