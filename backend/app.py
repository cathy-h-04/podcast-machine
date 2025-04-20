#!/usr/bin/env python3
"""
PDF to Audio Script Converter
------------------------------
A Flask API that converts PDF files to podcast, debate, or teaching scripts using Claude.
The system handles user preferences and validates PDF content suitability.
Only processes 'summaritive' mode requests.
"""

from flask import Flask
from flask_cors import CORS
import os
from dotenv import load_dotenv
from routes import pdf_processing

# Load environment variables from .env file
load_dotenv()

# Create Flask app
app = Flask(__name__)

# Configure CORS to allow requests from localhost:5173
CORS(app, resources={r"/*": {"origins": "http://localhost:5173"}})

# Set maximum content length
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024  # 20MB limit


# Register routes
@app.route("/generate", methods=["POST"])
def generate_script():
    return pdf_processing.generate_script_route()


if __name__ == "__main__":
    # Ensure the system prompt template files exist
    base_dir = os.path.dirname(os.path.abspath(__file__))
    prompt_files = [
        os.path.join(base_dir, "podcast_prompt.txt"),
        os.path.join(base_dir, "debate_prompt.txt"),
        os.path.join(base_dir, "duck_prompt.txt"),
    ]

    for prompt_path in prompt_files:
        if not os.path.exists(prompt_path):
            filename = os.path.basename(prompt_path)
            print(f"WARNING: System prompt template file not found at {prompt_path}")
            print(f"Please create the {filename} file before running the application.")
            exit(1)

    # Start the application
    port = int(os.getenv("PORT", 6000))
    app.run(host="0.0.0.0", port=port, debug=True)
