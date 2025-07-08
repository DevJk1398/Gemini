import discord
from discord.ext import commands
import google.generativeai as genai
from flask import Flask
import threading
import os
from dotenv import load_dotenv
import asyncio

# Load environment variables
load_dotenv()
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PORT = int(os.getenv("PORT", 5000))

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Set up Discord bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Set up Flask app
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

# Bot events
@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

# Bot commands
@bot.command(name='ask')
async def ask_gemini(ctx, *, question):
    try:
        # Generate response from Gemini
        response = model.generate_content(question)
        # Send response (split if too long)
        if len(response.text) > 2000:
            parts = [response.text[i:i+2000] for i in range(0, len(response.text), 2000)]
            for part in parts:
                await ctx.send(part)
        else:
            await ctx.send(response.text)
    except Exception as e:
        await ctx.send(f"Error: {str(e)}")

# Function to run Flask app
def run_flask():
    app.run(host='0.0.0.0', port=PORT)

# Main function to start both bot and Flask
def main():
    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Start Discord bot
    bot.run(DISCORD_BOT_TOKEN)

if __name__ == "__main__":
    main()
