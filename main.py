import os
import asyncio
import logging
import aiohttp
import discord

# Configurações e constantes
GUILD_NAME = "Os Viriatos"
GUILD_ID = "sMgQvZkqQy-QdnRZ1GmfFw"  # ID único da guilda Os Viriatos no Albion Online
MIN_PLAYERS = 5  # Número mínimo de jogadores da guilda para considerar a batalha válida

# Configuração do logger para debug
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")

# Inicialização do client do Discord
intents = discord.Intents.default()
intents.message_content = True  # necessário para enviar mensagens
client = discord.Client(intents=intents)

# Canal do Discord para enviar notificações (obtido das variáveis de ambiente)
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", "0"))
# Token do bot do Discord (variável de ambiente)
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Variável para controlar a última batalha já notificada (para evitar duplicações)
last_battle_id = 0

async def fetch_guild_battles(session):
    """Busca as batalhas recentes da guilda Os Viriatos usando a API do Albion Online."""
    # Endpoint da API para listar batalhas envolvendo a guilda especificada.
    # Usamos sort=recent para obter as mais recentes e limit=50 para abranger suficientes.
    url = (f"https://gameinfo-ams.albiononline.com/api/gameinfo/battles"
           f"?limit=50&sort=recent&guildId={GUILD_ID}")
    async with session.get(url) as response:
        if response.status != 200:
            logging.error(f"Falha ao obter lista de batalhas (status {response.status})")
            return []
        data = await response.json()
        # 'data' deve ser uma lista de batalhas com campos básicos (id, totalKills, totalFame, etc.)
        return data

async def fetch_battle_details(session, battle_id):
    """Busca os detalhes de uma batalha específica por ID."""
    url = f"https://gameinfo-ams.albiononline.com/api/gameinfo/battles/{battle_id}"
    async with session.get(url) as response:
        if response.status != 200:
            logging.error(f"Falha ao obter detalhes da batalha {battle_id} (status {response.status})")
            return None
        details = await response.json()
        return details

async def check_new_battles():
    """Tarefa de verificação periódica de novas batalhas da guilda Os Viriatos."""
    global last_battle_id
    async with aiohttp.ClientSession() as session:
        # Loop infinito para checar continuamente
        while True:
            try:
                battles = await fetch_guild_battles(session)
                if not battles:
                    # Se não conseguiu obter dados, espera e tenta novamente
                    await asyncio.sleep(60)
                    continue
                # A API retorna as batalhas ordenadas pela mais recente primeiro:contentReference[oaicite:6]{index=6}.
                # Filtra apenas as batalhas com ID maior do que o último já processado.
                new_battles = [b for b in battles if b.get('id') and b['id'] > last_battle_id]
                # Ordena as novas batalhas por ID (cronologicamente) para postar na ordem correta
                new_battles.sort(key=lambda b: b['id'])
                for battle in new_battles:
                    battle_id = battle['id']
                    # Obtém detalhes da batalha para verificar contagem de jogadores da guilda
                    details = await fetch_battle_details(session, battle_id)
                    if not details:
                        continue  # pula se não conseguiu pegar detalhes
                    # Procura a guilda Os Viriatos na lista de guildas da batalha
                    guild_entry = None
                    for guild in details.get('guilds', []):
                        if guild.get('name') == GUILD_NAME:
                            guild_entry = guild
                            break
                    # Obtém o número de jogadores da guilda na batalha
                    if guild_entry:
                        players_count = guild_entry.get('players') or guild_entry.get('memberCount') or 0
                    else:
                        # Se a guilda não foi encontrada na seção de guildas (improvável),
                        # faz contagem manual nos jogadores
                        players_count = sum(1 for player in details.get('players', [])
                                             if player.get('guildName') == GUILD_NAME)
                    logging.debug(f"Guilda '{GUILD_NAME}' encontrada na batalha {battle_id} com {players_count} jogadores.")
                    # Verifica se atende ao critério de mínimo de jogadores
                    if players_count >= MIN_PLAYERS:
                        # Prepara a mensagem de anúncio da batalha
                        total_kills = details.get('totalKills', 0)
                        total_fame = details.get('totalFame', 0)
                        battle_time = details.get('startTime', '')  # data/hora de início da batalha
                        message = (f"🔴 **Nova batalha envolvendo a guilda {GUILD_NAME}!**\n"
                                   f"> **Batalha ID:** {battle_id}\n"
                                   f"> **Início:** {battle_time}\n"
                                   f"> **Participação da guilda:** {players_count} membros\n"
                                   f"> **Abates (Kills):** {total_kills}\n"
                                   f"> **Fama Total:** {total_fame}\n"
                                   f"> *Detalhes completos:* <https://eu.albionbattles.com/battles/{battle_id}>")
                        # Envia a mensagem para o canal designado no Discord
                        channel = client.get_channel(DISCORD_CHANNEL_ID)
                        if channel:
                            await channel.send(message)
                            logging.info(f"Batalha {battle_id} notificada no Discord (guilda com {players_count} membros).")
                        else:
                            logging.error("Canal do Discord inválido. Verifique o DISCORD_CHANNEL_ID.")
                    # Atualiza o último ID processado para não repetir esta batalha no futuro
                    if battle_id > last_battle_id:
                        last_battle_id = battle_id
                # Aguarda um minuto até a próxima checagem
                await asyncio.sleep(60)
            except Exception as e:
                logging.exception(f"Erro no loop de verificação de batalhas: {e}")
                # Em caso de erro, espera alguns segundos antes de retomar para evitar loop rápido em falhas
                await asyncio.sleep(30)

@client.event
async def on_ready():
    """Evento chamado quando o bot se conecta com sucesso ao Discord."""
    logging.info(f"Bot conectado como {client.user} (ID: {client.user.id})")
    # Inicia a tarefa de monitoramento de batalhas em background
    client.loop.create_task(check_new_battles())

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        logging.error("DISCORD_TOKEN não encontrado. Por favor, defina o token do bot nas variáveis de ambiente.")
    else:
        client.run(DISCORD_TOKEN)
