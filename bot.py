import os
import threading
import time
import asyncio # Required for Discord.py async operations

from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
import discord # Import discord.py library
from dotenv import load_dotenv

# --- Load Environment Variables ---
# This will load variables from a .env file if it exists.
# For production, environment variables are typically set directly on the hosting platform.
load_dotenv()

# --- Configuration ---
# Get Flask port from environment variable, default to 8080 if not set
FLASK_PORT = int(os.environ.get('PORT', 8080))

# Get Gemini API key from environment variable
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

# Get Discord Bot Token from environment variable
DISCORD_BOT_TOKEN = os.environ.get('DISCORD_BOT_TOKEN')

# --- Validation and Initialization ---
if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY environment variable not set.")
    print("Please set it before running the application (e.g., export GEMINI_API_KEY='your_key').")
    print("You can get an API key from Google AI Studio: https://aistudio.google.com/")
    exit(1) # Exit if critical variable is missing

if not DISCORD_BOT_TOKEN:
    print("Error: DISCORD_BOT_TOKEN environment variable not set.")
    print("Please set it before running the application (e.g., export DISCORD_BOT_TOKEN='your_token').")
    print("Get your bot token from Discord Developer Portal: https://discord.com/developers/applications")
    exit(1) # Exit if critical variable is missing

# Configure the Gemini API
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-pro')

# Configure the Discord Bot
intents = discord.Intents.default()
intents.message_content = True # REQUIRED to read message content from users
discord_client = discord.Client(intents=intents)

# --- Flask App Setup ---
app = Flask(__name__) # __name__ correctly tells Flask where to find 'templates'

# --- Flask Routes ---

@app.route('/')
def index():
    """Renders the main HTML page for the chatbot."""
    # This is the line that's causing the error if index.html isn't found
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Attempting to render index.html...")
    # Double-check template search path (for advanced debugging if needed)
    # print(f"Flask template search paths: {app.template_folder}")
    return render_template('index.html')

@app.route('/ask_gemini_web', methods=['POST'])
def ask_gemini_web():
    """Web endpoint to receive user questions and send them to the Gemini API."""
    user_question = request.json.get('question')
    if not user_question:
        return jsonify({"error": "No question provided"}), 400

    try:
        response = gemini_model.generate_content(user_question)
        return jsonify({"response": response.text})
    except Exception as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Error calling Gemini API from web: {e}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route('/health')
def health_check():
    """Health check endpoint for keep-alive monitoring."""
    discord_status = "connected" if discord_client.is_ready() else "disconnected"
    return jsonify({
        "status": "healthy",
        "message": "Flask server and bot are running.",
        "discord_status": discord_status,
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S IST')
    })

def run_flask_app():
    """Function to run the Flask application in a separate thread."""
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Starting Flask server on port {FLASK_PORT}...")
    # Use_reloader=False is crucial in a threaded environment to prevent Flask from
    # trying to restart itself, which can cause issues with multiple threads.
    # debug=False for production deployment.
    app.run(host='0.0.0.0', port=FLASK_PORT, debug=False, use_reloader=False)

# --- Discord Bot Events ---

@discord_client.event
async def on_ready():
    """Called when the bot successfully connects to Discord."""
    print(f'[{time.strftime("%Y-%m-%d %H:%M:%S")}] Logged in as {discord_client.user} (ID: {discord_client.user.id})')
    print('------')

@discord_client.event
async def on_message(message):
    """Called when a message is sent in a channel the bot can see."""
    if message.author == discord_client.user: # Ignore messages from self
        return

    # Respond to messages starting with '!gemini '
    if message.content.startswith('!gemini '):
        user_question = message.content[len('!gemini '):].strip()

        if not user_question:
            await message.channel.send("Please provide a question after `!gemini`.")
            return

        try:
            await message.channel.send(f"Thinking... (asking Gemini about: '{user_question}')")
            response = gemini_model.generate_content(user_question)
            gemini_text = response.text

            # Discord message limit is 2000 characters
            if len(gemini_text) > 2000:
                await message.channel.send("Response is too long. Sending in parts:")
                for chunk in [gemini_text[i:i+1990] for i in range(0, len(gemini_text), 1990)]:
                    await message.channel.send(f"```\n{chunk}\n```") # Use code blocks for better formatting
            else:
                await message.channel.send(gemini_text)

        except Exception as e:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Error processing Discord message with Gemini: {e}")
            await message.channel.send(f"Sorry, an error occurred while trying to get a response from Gemini: {e}")

# --- Main Execution Block ---

def start_discord_bot_in_loop():
    """Helper function to run the Discord bot in its own asyncio event loop."""
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Starting Discord bot...")
    try:
        # discord_client.run() is a blocking call
        discord_client.run(DISCORD_BOT_TOKEN)
    except discord.errors.LoginFailure:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Discord Login Error: Invalid token or intents not configured correctly.")
        print("Ensure 'Message Content Intent' is enabled in your bot's settings on Discord Developer Portal.")
        os._exit(1) # Critical error, exit the process
    except Exception as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] An unexpected error occurred with Discord bot: {e}")
        os._exit(1) # Critical error, exit the process

if __name__ == "__main__":
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Starting application (Flask + Gemini + Discord Bot)...")

    # Start the Flask app in a separate daemon thread
    flask_thread = threading.Thread(target=run_flask_app)
    flask_thread.daemon = True # Daemon threads exit when the main program exits
    flask_thread.start()
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Flask server thread initiated on port {FLASK_PORT}.")

    # Start the Discord bot in the main thread.
    # This call is blocking and will keep the main process alive.
    start_discord_bot_in_loop()

    # This part of the code will only be reached if the Discord bot's event loop stops
    # (e.g., due to an unhandled error or explicit shutdown).
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Application finished.")

