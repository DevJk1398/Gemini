import os
import threading
import time
import asyncio # Required for Discord.py async operations

from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
import discord # Import discord.py library
from dotenv import load_dotenv

# --- Load Environment Variables ---
load_dotenv()

# --- Configuration ---
FLASK_PORT = int(os.environ.get('PORT', 8080))
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
DISCORD_BOT_TOKEN = os.environ.get('DISCORD_BOT_TOKEN')

# --- Validation ---
if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY environment variable not set.")
    print("Please set it before running the application.")
    print("You can get an API key from Google AI Studio: https://aistudio.google.com/")
    exit(1)

if not DISCORD_BOT_TOKEN:
    print("Error: DISCORD_BOT_TOKEN environment variable not set.")
    print("Please set it before running the application.")
    print("Get your bot token from Discord Developer Portal: https://discord.com/developers/applications")
    exit(1)

# --- Configure Gemini API ---
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-pro')

# --- Configure Discord Bot ---
# intents specify what events your bot wants to receive from Discord
# discord.Intents.default() is a good starting point.
# You MUST enable 'Message Content Intent' in your Discord Developer Portal
# if your bot needs to read message content to respond to commands.
intents = discord.Intents.default()
intents.message_content = True # Required to read message content
discord_client = discord.Client(intents=intents)

# --- Flask App Setup ---
app = Flask(__name__)

# --- Flask Routes ---

@app.route('/')
def index():
    """Renders the main HTML page for the chatbot (optional, for web interface)."""
    return render_template('index.html')

@app.route('/ask_gemini_web', methods=['POST'])
def ask_gemini_web():
    """
    Web endpoint to receive user questions and send them to the Gemini API.
    Returns the Gemini's response for the web UI.
    """
    user_question = request.json.get('question')
    if not user_question:
        return jsonify({"error": "No question provided"}), 400

    try:
        response = gemini_model.generate_content(user_question)
        return jsonify({"response": response.text})
    except Exception as e:
        print(f"Error calling Gemini API from web: {e}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route('/health')
def health_check():
    """Health check endpoint for keep-alive monitoring."""
    # We can also check Discord bot's status if needed
    discord_status = "connected" if discord_client.is_ready() else "disconnected"
    return jsonify({
        "status": "healthy",
        "message": "Flask server and bot are running.",
        "discord_status": discord_status
    })

def run_flask_app():
    """Function to run the Flask application in a separate thread."""
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Starting Flask server on port {FLASK_PORT}...")
    app.run(host='0.0.0.0', port=FLASK_PORT, debug=False) # debug=False for production

# --- Discord Bot Events ---

@discord_client.event
async def on_ready():
    """Called when the bot successfully connects to Discord."""
    print(f'[{time.strftime("%Y-%m-%d %H:%M:%S")}] Logged in as {discord_client.user} (ID: {discord_client.user.id})')
    print('------')

@discord_client.event
async def on_message(message):
    """Called when a message is sent in a channel the bot can see."""
    # Don't respond to ourselves
    if message.author == discord_client.user:
        return

    # Basic command handling: !gemini <your question>
    if message.content.startswith('!gemini'):
        user_question = message.content[len('!gemini'):].strip()

        if not user_question:
            await message.channel.send("Please provide a question after `!gemini`.")
            return

        try:
            # Use Gemini to generate a response
            await message.channel.send(f"Thinking... (asking Gemini about: '{user_question}')")
            response = gemini_model.generate_content(user_question)
            gemini_text = response.text

            # Send Gemini's response back to the Discord channel
            # Split long messages if necessary, as Discord has a 2000 character limit
            if len(gemini_text) > 2000:
                await message.channel.send("Response is too long for a single Discord message. Sending in parts...")
                for chunk in [gemini_text[i:i+1990] for i in range(0, len(gemini_text), 1990)]:
                    await message.channel.send(f"```\n{chunk}\n```") # Use code blocks for readability
            else:
                await message.channel.send(gemini_text)

        except Exception as e:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Error processing Discord message: {e}")
            await message.channel.send(f"Sorry, an error occurred while trying to get a response: {e}")

# --- Main Execution Block ---

# Since discord.py uses asyncio, we need to manage the event loop.
# We'll run the Discord bot within the main thread's asyncio loop.
# The Flask app will run in a separate regular thread.

def start_discord_bot():
    """Function to start the Discord bot's event loop."""
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Starting Discord bot...")
    # This is a blocking call and keeps the bot running
    try:
        discord_client.run(DISCORD_BOT_TOKEN)
    except discord.errors.LoginFailure:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Discord Login Error: Invalid token or intents not configured correctly.")
        print("Please check your DISCORD_BOT_TOKEN and ensure 'Message Content Intent' is enabled in Developer Portal.")
        os._exit(1) # Exit the process if login fails
    except Exception as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] An unexpected error occurred with Discord bot: {e}")
        os._exit(1)


if __name__ == "__main__":
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Starting application (Flask + Gemini + Discord Bot)...")

    # 1. Start the Flask app in a separate daemon thread
    flask_thread = threading.Thread(target=run_flask_app)
    flask_thread.daemon = True
    flask_thread.start()
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Flask server thread initiated on port {FLASK_PORT}.")

    # 2. Start the Discord bot in the main thread
    # The `discord_client.run()` method is blocking and manages the bot's event loop.
    start_discord_bot()

    # The code below this line will only be reached if discord_client.run() somehow stops,
    # or if the application is manually terminated (e.g., via Ctrl+C).
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Application finished.")

