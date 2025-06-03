import os
import asyncio
import logging
import aiohttp
import discord

# Configurações e constantes
GUILD_NAME = "Os Viriatos"
GUILD_ID = "sMgQvZkqQy-QdnRZ1GmfFw"
MIN_PLAYERS = 5

# Logger
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")

# Discord bot
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", "0"))
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

last_battle_id = 0

async def fetch_guild_battles(session):
    url = (f"https://gameinfo-ams.albiononline.com/api/gameinfo/battles"
           f"?limit=50&sort=recent&guildId={GUILD_ID}")
    headers = {"User-Agent": "Mozilla/5.0"}
    async with session.get(url, headers=headers) as response:
        if response.status != 200:
            logging.error(f"Falha ao obter lista de batalhas (status {response.status})")
            return []
        return await response.json()

async def fetch_battle_details(session, battle_id):
    url = f"https://gameinfo-ams.albiononline.com/api/gameinfo/battles/{battle_id}"
    headers = {"User-Agent": "Mozilla/5.0"}
    async with session.get(url, headers=headers) as response:
        if response.status != 200:
            logging.error(f"Falha ao obter detalhes da batalha {battle_id} (status {response.status})")
            return None
        return await response.json()

async def check_new_battles():
    global last_battle_id
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                battles = await fetch_guild_battles(session)
                if not battles:
                    await asyncio.sleep(60)
                    continue

                new_battles = [b for b in battles if b.get('id') and b['id'] > last_battle_id]
                new_battles.sort(key=lambda b: b['id'])

                for battle in new_battles:
                    battle_id = battle['id']
                    details = await fetch_battle_details(session, battle_id)
                    if not details:
                        continue

                    guild_entry = None
                    for guild in details.get('guilds', []):
                        if guild.get('name') == GUILD_NAME:
                            guild_entry = guild
                            break

                    if guild_entry:
                        players_count = guild_entry.get('players') or guild_entry.get('memberCount') or 0
                    else:
                        players_count = sum(1 for player in details.get('players', [])
                                             if player.get('guildName') == GUILD_NAME)

                    logging.debug(f"Guilda '{GUILD_NAME}' encontrada na batalha {battle_id} com {players_count} jogadores.")

                    if players_count >= MIN_PLAYERS:
                        total_kills = details.get('totalKills', 0)
                        total_fame = details.get('totalFame', 0)
                        battle_time = details.get('startTime', '')
                        message = (
                            f"🏴 **Nova batalha de {GUILD_NAME}!**\n"
                            f"> 🆔 Batalha ID: `{battle_id}`\n"
                            f"> 🕒 Início: `{battle_time}`\n"
                            f"> 👥 Participação: `{players_count}` membros\n"
                            f"> ⚔️ Abates: `{total_kills}`\n"
                            f"> 💰 Fama Total: `{total_fame}`\n"
                            f"> 🔗 Detalhes: https://eu.albionbattles.com/battles/{battle_id}"
                        )
                        channel = client.get_channel(DISCORD_CHANNEL_ID)
                        if channel:
                            await channel.send(message)
                            logging.info(f"Batalha {battle_id} publicada com sucesso!")
                        else:
                            logging.error("Canal do Discord inválido. Verifique o DISCORD_CHANNEL_ID.")

                    if battle_id > last_battle_id:
                        last_battle_id = battle_id

                await asyncio.sleep(60)

            except Exception as e:
                logging.exception(f"Erro no loop de verificação de batalhas: {e}")
                await asyncio.sleep(30)

@client.event
async def on_ready():
    logging.info(f"🤖 Bot conectado como {client.user} (ID: {client.user.id})")
    client.loop.create_task(check_new_battles())

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        logging.error("❌ DISCORD_TOKEN não encontrado. Define nas variáveis de ambiente.")
    else:
        client.run(DISCORD_TOKEN)
