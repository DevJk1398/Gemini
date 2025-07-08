import os
import discord
from discord.ext import commands
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure Discord bot intents
intents = discord.Intents.default()
intents.message_content = True  # Required to read message content
intents.members = True # If you need member-related events

# Initialize Discord bot
bot = commands.Bot(command_prefix="!", intents=intents)

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables.")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro') # You can choose other models like 'gemini-pro-vision' for image support

# Store conversation history for each channel/user
conversation_history = {}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    print('Bot is ready to receive commands!')

@bot.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return

    # Optionally, restrict to specific channels or mentions
    # For simplicity, we'll respond to any message in a channel the bot can see.
    # To make it respond only when mentioned:
    # if not bot.user.mentioned_in(message):
    #     await bot.process_commands(message) # Important to process other commands
    #     return

    # Get conversation history for the current channel/user
    # Using message.channel.id for channel-specific context
    if message.channel.id not in conversation_history:
        conversation_history[message.channel.id] = model.start_chat(history=[])
    
    chat = conversation_history[message.channel.id]

    try:
        # Send message to Gemini and get response
        response = await chat.send_message_async(message.content)
        await message.channel.send(response.text)
    except Exception as e:
        print(f"Error interacting with Gemini API: {e}")
        await message.channel.send("Sorry, I encountered an error trying to process that. Please try again later.")
    
    # This line is crucial to allow other commands to be processed if you have any
    await bot.process_commands(message)

# Example command to clear conversation history
@bot.command(name='clearhistory')
async def clear_history(ctx):
    if ctx.channel.id in conversation_history:
        del conversation_history[ctx.channel.id]
        await ctx.send("Conversation history for this channel has been cleared.")
    else:
        await ctx.send("No conversation history to clear for this channel.")

# Run the bot
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
if not DISCORD_BOT_TOKEN:
    raise ValueError("DISCORD_BOT_TOKEN not found in environment variables.")

bot.run(DISCORD_BOT_TOKEN)
