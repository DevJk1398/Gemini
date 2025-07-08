import discord
from discord.ext import commands
import google.generativeai as genai
from flask import Flask
import threading
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PORT = int(os.getenv("PORT", 5000))

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Set up Discord bot with no command prefix
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='', intents=intents, case_insensitive=True)

# Set up Flask app
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

# Set to keep track of active channels
active_channels = set()

# Bot events
@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

# Command to enable bot responses in a channel
@bot.command(name='berry on')
async def berry_on(ctx):
    active_channels.add(ctx.channel.id)
    await ctx.send("Berry is now active in this channel! I'll respond to all messages here.")

# Command to disable bot responses in a channel
@bot.command(name='berry off')
async def berry_off(ctx):
    active_channels.discard(ctx.channel.id)
    await ctx.send("Berry is now off in this channel. I won't respond to messages here unless activated again.")

# Handle messages
@bot.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return

    # Process commands first
    await bot.process_commands(message)

    # Check if message is in DMs or an active channel
    if isinstance(message.channel, discord.DMChannel) or message.channel.id in active_channels:
        # Skip if message is a command ("berry on" or "berry off")
        if message.content.lower() in ['berry on', 'berry off']:
            return
        
        try:
            # Generate response from Gemini
            response = model.generate_content(message.content)
            # Send response (split if too long)
            if len(response.text) > 2000:
                parts = [response.text[i:i+2000] for i in range(0, len(response.text), 2000)]
                for part in parts:
                    await message.channel.send(part)
            else:
                await message.channel.send(response.text)
        except Exception as e:
            await message.channel.send(f"Error: {str(e)}")

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
