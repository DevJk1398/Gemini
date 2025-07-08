import os
import threading
import time
from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
from dotenv import load_dotenv # For loading environment variables from .env file

# --- Load Environment Variables ---
# This will load variables from a .env file if it exists.
# For production, environment variables are typically set directly on the hosting platform.
load_dotenv()

# --- Configuration ---
# Get Flask port from environment variable, default to 8080 if not set
FLASK_PORT = int(os.environ.get('PORT', 8080))

# Get Gemini API key from environment variable
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY environment variable not set.")
    print("Please set it before running the application.")
    print("You can get an API key from Google AI Studio: https://aistudio.google.com/")
    exit(1)

# Configure the Gemini API
genai.configure(api_key=GEMINI_API_KEY)

# Initialize the Generative Model
# You can choose different models like 'gemini-pro', 'gemini-pro-vision', etc.
# 'gemini-pro' is good for text-only conversations.
model = genai.GenerativeModel('gemini-pro')

# --- Flask App Setup for API and Keep-Alive ---
app = Flask(__name__)

# --- Flask Routes ---

@app.route('/')
def index():
    """Renders the main HTML page for the chatbot."""
    return render_template('index.html')

@app.route('/ask_gemini', methods=['POST'])
def ask_gemini():
    """
    Endpoint to receive user questions and send them to the Gemini API.
    Returns the Gemini's response.
    """
    user_question = request.json.get('question')

    if not user_question:
        return jsonify({"error": "No question provided"}), 400

    try:
        # Generate content using the Gemini model
        response = model.generate_content(user_question)

        # Access the generated text
        gemini_response_text = response.text

        return jsonify({"response": gemini_response_text})

    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route('/health')
def health_check():
    """
    Health check endpoint for keep-alive monitoring.
    Returns a simple JSON status.
    """
    return jsonify({"status": "healthy", "message": "Flask server and bot are running."})

def run_flask_app():
    """Function to run the Flask application in a separate thread."""
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Starting Flask server on port {FLASK_PORT}...")
    # Run Flask on all available interfaces (0.0.0.0)
    # debug=False for production use; set to True for development if needed for auto-reloading
    app.run(host='0.0.0.0', port=FLASK_PORT, debug=False)

# --- Main Bot Logic (Optional, for Background Tasks) ---
# If your "bot" has background tasks that run independently of web requests,
# you can define them here. For a purely web-based bot, this might be empty.
def run_background_bot_tasks():
    """
    This function can be used for any long-running, non-web-request-driven
    tasks your bot might perform (e.g., scheduled checks, monitoring, etc.).
    """
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Starting background bot tasks... (simulated)")
    while True:
        # In a real bot, this could involve:
        # - Checking a database
        # - Performing routine maintenance
        # - Sending proactive messages based on events
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Bot background task running... (simulated)")
        time.sleep(300) # Sleep for 5 minutes (300 seconds)

# --- Main Execution Block ---
if __name__ == "__main__":
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Starting Flask + Gemini application...")

    # Start the Flask app in a separate thread
    # This keeps the web server running for API calls and health checks.
    flask_thread = threading.Thread(target=run_flask_app)
    flask_thread.daemon = True # Allows the main program to exit cleanly
    flask_thread.start()
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Flask server thread initiated.")

    # Start any background bot tasks in another separate thread (optional)
    # If your "bot" is purely driven by web requests, you might not need this.
    background_bot_thread = threading.Thread(target=run_background_bot_tasks)
    background_bot_thread.daemon = True
    background_bot_thread.start()
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Background bot tasks thread initiated (if applicable).")

    # Keep the main thread alive. This is crucial if your bot tasks
    # are primarily thread-based and not a single blocking call like client.run()
    # for a Discord bot. For a purely Flask app, the main thread can just exit
    # after starting the Flask thread, but this is safer for "bot" scenarios.
    try:
        while True:
            time.sleep(1) # Keep main thread alive
    except KeyboardInterrupt:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Application interrupted. Shutting down.")
    finally:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Application finished.")
