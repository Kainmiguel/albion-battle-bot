from keep_alive import keep_alive
import requests
import time
from datetime import datetime
import json
import os

GUILD_ID = "sMgQvZkqQy-QdnRZ1GmfFw"
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
EVENTS_API = f"https://gameinfo.albiononline.com/api/gameinfo/guilds/{GUILD_ID}/deaths?limit=50"
CHECK_INTERVAL = 180
EVENT_HISTORY_FILE = "posted_events.json"

keep_alive()

try:
    with open(EVENT_HISTORY_FILE, "r") as f:
        posted_ids = set(json.load(f))
except FileNotFoundError:
    posted_ids = set()

def get_recent_deaths():
    response = requests.get(EVENTS_API)
    return response.json() if response.status_code == 200 else []

def group_deaths(deaths):
    grouped = []
    for death in deaths:
        if death["EventId"] in posted_ids:
            continue
        ts = datetime.strptime(death["TimeStamp"], "%Y-%m-%dT%H:%M:%S")
        found = False
        for group in grouped:
            if abs((ts - group["time"]).total_seconds()) <= 120 and death["Location"] == group["location"]:
                group["deaths"].append(death)
                found = True
                break
        if not found:
            grouped.append({"time": ts, "location": death["Location"], "deaths": [death]})
    return grouped

def format_embed():
    embed = {
        "title": "🏴 NOVA BATALHA DE Os Viriatos",
        "description": (
            "👉 Depositem o loot na tab da guild\n"
            "📺 Postem as vossas VODS\n"
            "✍️ A vossa presença foi anotada"
        ),
        "url": "https://europe.albionbb.com/?search=Os+Viriatos",
        "image": {
            "url": "https://cdn.discordapp.com/attachments/1366525638621528074/1379488133355147375/albion_zvz.jpeg"
        },
        "color": 0
    }
    return {"embeds": [embed]}

def post_to_discord(embed):
    if not WEBHOOK_URL:
        print("ERRO: WEBHOOK_URL não está definida.")
        return False
    res = requests.post(WEBHOOK_URL, json=embed)
    return res.status_code in (200, 204)

def save_ids():
    with open(EVENT_HISTORY_FILE, "w") as f:
        json.dump(list(posted_ids), f)

def main_loop():_
