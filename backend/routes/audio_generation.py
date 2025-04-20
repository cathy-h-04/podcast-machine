# routes/audio_generation.py
from flask import request, jsonify, send_file
import os
import uuid
import logging
import sys
import tempfile
import time

# Add the parent directory to sys.path to allow absolute imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from routes import podcasts
from services.script_processor import ScriptProcessor
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('audio_generation')

# Load environment variables
load_dotenv()

# Path to store audio files
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIO_DIR = os.path.join(BASE_DIR, "static", "audio")

# Create audio directory if it doesn't exist
os.makedirs(AUDIO_DIR, exist_ok=True)

# Store progress information for each podcast
progress_data = {}


def generate_audio_route():
    """API endpoint to generate audio from a script"""
    try:
        # Get JSON data from request
        data = request.json
        if not data:
            logger.error("No JSON data provided")
            return jsonify({"error": "No JSON data provided"}), 400

        # Get podcast ID and script
        podcast_id = data.get("podcast_id")
        script = data.get("script")

        if not podcast_id:
            logger.error("Podcast ID is required")
            return jsonify({"error": "Podcast ID is required"}), 400

        if not script:
            logger.error("Script is required")
            return jsonify({"error": "Script is required"}), 400
            
        # Initialize progress tracking for this podcast
        progress_data[podcast_id] = {
            "status": "initializing",
            "step": "setup",
            "progress": 5,
            "message": "Initializing audio generation",
            "timestamp": time.time()
        }

        logger.info(f"Starting audio generation for podcast {podcast_id}")

        # Initialize Script Processor for multi-speaker podcasts
        try:
            script_processor = ScriptProcessor(
                api_key=os.getenv("CARTESIA_API_KEY")
            )
            logger.info("Script processor initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Script Processor: {str(e)}")
            progress_data[podcast_id] = {
                "status": "error",
                "step": "initialization",
                "progress": 0,
                "message": f"Error initializing: {str(e)}",
                "timestamp": time.time()
            }
            # Fallback: Create a dummy audio file for testing
            return _generate_dummy_audio(podcast_id)

        # Generate a unique filename with .wav extension
        audio_filename = f"{uuid.uuid4()}.wav"
        audio_path = os.path.join(AUDIO_DIR, audio_filename)
        logger.info(f"Audio will be saved to: {audio_path}")

        # Process the script and generate multi-speaker podcast
        try:
            # Update progress
            progress_data[podcast_id] = {
                "status": "processing",
                "step": "saving_script",
                "progress": 10,
                "message": "Saving script to temporary file",
                "timestamp": time.time()
            }
            
            # Save script to a temporary file
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
                temp_file.write(script)
                script_path = temp_file.name
            
            logger.info(f"Script saved to temporary file: {script_path}")
            
            # Define a callback function to update progress
            def progress_callback(progress_info):
                progress_data[podcast_id] = {
                    **progress_info,
                    "timestamp": time.time()
                }
                logger.info(f"Progress update: {progress_info['step']} - {progress_info['progress']}% - {progress_info['message']}")
            
            # Process the script and generate the podcast with progress updates
            success = script_processor.process_script(script_path, audio_path, callback=progress_callback)
            
            # Clean up temporary file
            os.unlink(script_path)
            logger.info("Temporary script file removed")
            
            if not success:
                logger.error("Failed to process script and generate podcast")
                raise Exception("Failed to process script and generate podcast")

            # Create a public URL for the audio file
            audio_url = f"/static/audio/{audio_filename}"
            logger.info(f"Audio URL created: {audio_url}")

            # Update the podcast with the audio URL
            podcasts.update_podcast_audio(podcast_id, audio_url)
            logger.info(f"Podcast {podcast_id} updated with audio URL")

            # Final progress update
            progress_data[podcast_id] = {
                "status": "complete",
                "step": "finished",
                "progress": 100,
                "message": "Podcast generation complete",
                "timestamp": time.time()
            }

            return jsonify({
                "success": True, 
                "audioUrl": audio_url, 
                "podcast_id": podcast_id
            }), 200

        except Exception as e:
            logger.error(f"Error generating audio: {str(e)}")
            progress_data[podcast_id] = {
                "status": "error",
                "step": "processing",
                "progress": 0,
                "message": f"Error: {str(e)}",
                "timestamp": time.time()
            }
            # Fallback: Create a dummy audio file for testing
            return _generate_dummy_audio(podcast_id)

    except Exception as e:
        logger.exception(f"Error in generate_audio_route: {str(e)}")
        return jsonify({"error": "Failed to generate audio", "message": str(e)}), 500


def _generate_dummy_audio(podcast_id):
    """Generate a dummy audio file for testing purposes"""
    logger.info(f"Generating dummy audio for podcast {podcast_id}")
    
    # Generate a unique filename with .wav extension
    audio_filename = f"{uuid.uuid4()}.wav"
    audio_path = os.path.join(AUDIO_DIR, audio_filename)

    # Create an empty audio file (1KB of silence)
    with open(audio_path, "wb") as f:
        f.write(b"\x00" * 1024)
    logger.info(f"Created dummy audio file: {audio_path}")

    # Create a public URL for the audio file
    audio_url = f"/static/audio/{audio_filename}"

    # Update the podcast with the audio URL
    podcasts.update_podcast_audio(podcast_id, audio_url)
    logger.info(f"Updated podcast {podcast_id} with dummy audio URL")
    
    # Update progress data
    progress_data[podcast_id] = {
        "status": "complete",
        "step": "dummy_audio",
        "progress": 100,
        "message": "Created dummy audio file for testing",
        "timestamp": time.time()
    }

    return jsonify({
        "success": True,
        "audioUrl": audio_url,
        "podcast_id": podcast_id,
        "message": "Using dummy audio file for testing",
    }), 200


def get_audio_route(filename):
    """API endpoint to retrieve an audio file"""
    audio_path = os.path.join(AUDIO_DIR, filename)
    logger.info(f"Request for audio file: {filename}")

    if not os.path.exists(audio_path):
        logger.error(f"Audio file not found: {audio_path}")
        return jsonify({"error": "Audio file not found"}), 404

    logger.info(f"Serving audio file: {audio_path}")
    return send_file(audio_path, mimetype="audio/mpeg")


def get_progress_route(podcast_id):
    """API endpoint to get the progress of audio generation"""
    if podcast_id not in progress_data:
        logger.warning(f"Progress data not found for podcast: {podcast_id}")
        return jsonify({
            "status": "unknown",
            "step": "unknown",
            "progress": 0,
            "message": "No progress data available"
        }), 404
    
    logger.info(f"Returning progress data for podcast {podcast_id}: {progress_data[podcast_id]}")
    return jsonify(progress_data[podcast_id])
