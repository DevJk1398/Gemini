from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import aiohttp
import asyncio

app = Flask(__name__)
COC_API_TOKEN = "your_coc_api_token"
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
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            data = loop.run_until_complete(fetch_player(tag))

            if "name" in data:
                msg.body(f"🏆 {data['name']} | TH: {data.get('townHallLevel')} | Trophies: {data.get('trophies')}")
            else:
                msg.body("❌ Player not found. Check the tag.")
        else:
            msg.body("Usage: /player #TAG")
    else:
        msg.body("👋 Welcome to CoC Bot! Use /player #TAG to get started.")

    return str(response)

if __name__ == "__main__":
    app.run(port=5000)
