from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import aiohttp
import asyncio
import os

app = Flask(__name__)

# Get API token from environment variable
COC_API_TOKEN = os.getenv("COC_API_TOKEN")
COC_PROXY = "https://cocproxy.royaleapi.dev"

async def fetch_player(tag):
    headers = {"Authorization": f"Bearer {COC_API_TOKEN}"}
    url = f"{COC_PROXY}/v1/players/{tag.replace('#', '%23')}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            return await resp.json()

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    incoming_msg = request.values.get('Body', '').strip()
    response = MessagingResponse()
    msg = response.message()

    if incoming_msg.lower().startswith("/player"):
        parts = incoming_msg.split()
        if len(parts) == 2:
            tag = parts[1]
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                data = loop.run_until_complete(fetch_player(tag))

                if "name" in data:
                    name = data.get("name")
                    town_hall = data.get("townHallLevel")
                    trophies = data.get("trophies")
                    msg.body(f"🏆 {name} | TH: {town_hall} | Trophies: {trophies}")
                else:
                    msg.body("❌ Player not found. Please check the tag.")
            except Exception as e:
                msg.body("⚠️ Error fetching player data.")
        else:
            msg.body("Usage: /player #TAG")
    else:
        msg.body("👋 Welcome to Clash Bot!\nUse /player #TAG to get player info.")

    return str(response)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
