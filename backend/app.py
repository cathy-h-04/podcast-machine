#!/usr/bin/env python3
"""
PDF to Audio Script Converter
------------------------------
A Flask API that converts PDF files to podcast, debate, or teaching scripts using Claude.
The system handles user preferences and validates PDF content suitability.
Only processes 'summaritive' mode requests.
Includes user authentication with registration and login functionality.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
from routes import (
    pdf_processing,
    auth,
    podcasts,
    audio_generation,
    cover_art_generation,
    replica,
)

# Load environment variables from .env file
load_dotenv()

# Create Flask app
app = Flask(__name__, static_folder="static")

# Configure CORS to allow requests from localhost:5173
CORS(app, resources={r"/*": {"origins": "http://localhost:5173"}})

# Set maximum content length
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024  # 20MB limit


# Register routes
@app.route("/generate", methods=["POST"])
def generate_script():
    return pdf_processing.generate_script_route()


@app.route("/api/script-progress/<process_id>", methods=["GET"])
def get_script_progress(process_id):
    return pdf_processing.get_script_progress_route(process_id)


# Authentication routes
@app.route("/api/register", methods=["POST"])
def register():
    return auth.register_route()


@app.route("/api/login", methods=["POST"])
def login():
    return auth.login_route()


@app.route("/api/logout", methods=["POST"])
def logout():
    return auth.logout_route()


# User prompts routes have been removed


# Podcast routes
@app.route("/api/podcasts", methods=["GET"])
def get_podcasts():
    return podcasts.get_podcasts_route()


@app.route("/api/podcasts/<podcast_id>", methods=["GET"])
def get_podcast(podcast_id):
    return podcasts.get_podcast_route(podcast_id)


@app.route("/api/podcasts/<podcast_id>", methods=["DELETE"])
def delete_podcast(podcast_id):
    return podcasts.delete_podcast_route(podcast_id)


@app.route("/api/podcasts/<podcast_id>/title", methods=["PUT"])
def update_podcast_title(podcast_id):
    data = request.get_json()
    new_title = data.get("title")

    if not new_title:
        return jsonify({"error": "Title is required"}), 400

    updated_podcast = podcasts.update_podcast_title(podcast_id, new_title)

    if not updated_podcast:
        return jsonify({"error": "Podcast not found"}), 404

    return jsonify({"success": True, "podcast": updated_podcast})


@app.route("/api/podcasts/<podcast_id>/listened", methods=["PUT"])
def toggle_podcast_listened(podcast_id):
    updated_podcast = podcasts.toggle_podcast_listened(podcast_id)

    if not updated_podcast:
        return jsonify({"error": "Podcast not found"}), 404

    return jsonify({"success": True, "podcast": updated_podcast})


# Audio generation routes
@app.route("/api/generate-audio", methods=["POST"])
def generate_audio():
    return audio_generation.generate_audio_route()


@app.route("/static/audio/<filename>", methods=["GET"])
def get_audio(filename):
    return audio_generation.get_audio_route(filename)


@app.route("/api/audio-progress/<podcast_id>", methods=["GET"])
def get_audio_progress(podcast_id):
    return audio_generation.get_progress_route(podcast_id)


# Cover Art Generation
@app.route("/api/generate-cover", methods=["POST"])
def generate_cover():
    return cover_art_generation.generate_cover_art()


# Replica Conversation Routes
@app.route("/api/conversations", methods=["POST"])
def start_conversation():
    return replica.start_conversation_route()


@app.route("/api/conversations", methods=["GET"])
def list_conversations():
    return replica.list_conversations_route()


@app.route("/api/conversations/<conversation_id>", methods=["GET"])
def get_conversation(conversation_id):
    return replica.get_conversation_route(conversation_id)


@app.route("/api/conversations/<conversation_id>/end", methods=["POST"])
def end_conversation(conversation_id):
    return replica.end_conversation_route(conversation_id)


@app.route("/api/conversations/<conversation_id>", methods=["DELETE"])
def delete_conversation(conversation_id):
    return replica.delete_conversation_route(conversation_id)


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
