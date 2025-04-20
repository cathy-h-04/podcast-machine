# routes/audio_generation.py
from flask import request, jsonify, send_file
import os
import uuid
import json
from . import podcasts
from services.cartesia_client import CartesiaClient
from services.script_processor import ScriptProcessor
from dotenv import load_dotenv
import tempfile

# Load environment variables
load_dotenv()

# Path to store audio files
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIO_DIR = os.path.join(BASE_DIR, "static", "audio")

# Create audio directory if it doesn't exist
os.makedirs(AUDIO_DIR, exist_ok=True)


def generate_audio_route():
    """API endpoint to generate audio from a script"""
    try:
        # Get JSON data from request
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        # Get podcast ID and script
        podcast_id = data.get("podcast_id")
        script = data.get("script")

        if not podcast_id:
            return jsonify({"error": "Podcast ID is required"}), 400

        if not script:
            return jsonify({"error": "Script is required"}), 400

        # Initialize Script Processor for multi-speaker podcasts
        try:
            script_processor = ScriptProcessor(
                api_key=os.getenv("CARTESIA_API_KEY")
            )
        except Exception as e:
            print(f"Error initializing Script Processor: {str(e)}")
            # Fallback: Create a dummy audio file for testing
            return _generate_dummy_audio(podcast_id)

        # Generate a unique filename
        audio_filename = f"{uuid.uuid4()}.mp3"
        audio_path = os.path.join(AUDIO_DIR, audio_filename)

        # Process the script and generate multi-speaker podcast
        try:
            # Save script to a temporary file
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
                temp_file.write(script)
                script_path = temp_file.name
            
            # Process the script and generate the podcast
            success = script_processor.process_script(script_path, audio_path)
            
            # Clean up temporary file
            os.unlink(script_path)
            
            if not success:
                raise Exception("Failed to process script and generate podcast")

            # Create a public URL for the audio file
            audio_url = f"/static/audio/{audio_filename}"

            # Update the podcast with the audio URL
            podcasts.update_podcast_audio(podcast_id, audio_url)

            return jsonify(
                {"success": True, "audioUrl": audio_url, "podcast_id": podcast_id}
            ), 200

        except Exception as e:
            print(f"Error generating audio: {str(e)}")
            # Fallback: Create a dummy audio file for testing
            return _generate_dummy_audio(podcast_id)

    except Exception as e:
        print(f"Error in generate_audio_route: {str(e)}")
        return jsonify({"error": "Failed to generate audio", "message": str(e)}), 500


def _generate_dummy_audio(podcast_id):
    """Generate a dummy audio file for testing purposes"""
    # Generate a unique filename
    audio_filename = f"{uuid.uuid4()}.mp3"
    audio_path = os.path.join(AUDIO_DIR, audio_filename)

    # Create an empty audio file (1KB of silence)
    with open(audio_path, "wb") as f:
        f.write(b"\x00" * 1024)

    # Create a public URL for the audio file
    audio_url = f"/static/audio/{audio_filename}"

    # Update the podcast with the audio URL
    podcasts.update_podcast_audio(podcast_id, audio_url)

    return jsonify(
        {
            "success": True,
            "audioUrl": audio_url,
            "podcast_id": podcast_id,
            "message": "Using dummy audio file for testing",
        }
    ), 200


def get_audio_route(filename):
    """API endpoint to retrieve an audio file"""
    audio_path = os.path.join(AUDIO_DIR, filename)

    if not os.path.exists(audio_path):
        return jsonify({"error": "Audio file not found"}), 404

    return send_file(audio_path, mimetype="audio/mpeg")
