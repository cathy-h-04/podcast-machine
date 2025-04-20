# routes/podcasts.py
import os
import json
import uuid
from datetime import datetime
from flask import jsonify, request, abort
import time

# Path to podcasts data file
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PODCASTS_DATA_PATH = os.path.join(BASE_DIR, "data", "podcasts.json")


def _load_podcasts():
    """Load podcasts from JSON file"""
    try:
        if os.path.exists(PODCASTS_DATA_PATH):
            with open(PODCASTS_DATA_PATH, "r") as f:
                data = json.load(f)
                return data.get("podcasts", [])
        return []
    except Exception as e:
        print(f"Error loading podcasts: {str(e)}")
        return []


def _save_podcasts(podcasts):
    """Save podcasts to JSON file"""
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(PODCASTS_DATA_PATH), exist_ok=True)

        with open(PODCASTS_DATA_PATH, "w") as f:
            json.dump({"podcasts": podcasts}, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving podcasts: {str(e)}")
        return False


def get_podcasts_route():
    """API route to get all podcasts"""
    podcasts = _load_podcasts()
    return jsonify({"podcasts": podcasts})


def get_podcast_route(podcast_id):
    """API route to get a specific podcast by ID"""
    podcasts = _load_podcasts()
    podcast = next((p for p in podcasts if p["id"] == podcast_id), None)

    if not podcast:
        return jsonify({"error": "Podcast not found"}), 404

    return jsonify({"podcast": podcast})


def save_podcast(title, format, people_count, script, audio_url=None):
    """Save a new podcast to the database"""
    podcasts = _load_podcasts()

    # Convert numeric people count to text representation for frontend
    people_text = "one"
    if people_count == 2:
        people_text = "two"
    elif people_count >= 3:
        people_text = "three"

    # Create a new podcast entry
    new_podcast = {
        "id": str(uuid.uuid4()),
        "title": title,
        "format": format.lower(),  # podcast, debate, or duck
        "peopleCount": people_text,
        "createdAt": datetime.now().isoformat(),
        "duration": calculate_duration(script),  # Calculate based on script length
        "audioUrl": audio_url or "#",  # Placeholder if no audio URL yet
        "script": script,
    }

    # Add to podcasts list and save
    podcasts.append(new_podcast)
    _save_podcasts(podcasts)

    return new_podcast


def calculate_duration(script):
    """Calculate approximate duration in seconds based on script length
    Average reading speed: ~150 words per minute
    """
    if not script:
        return 600  # Default 10 minutes if no script

    # Count words in script
    word_count = len(script.split())

    # Estimate duration in seconds (150 words per minute)
    duration_seconds = int((word_count / 150) * 60)

    # Ensure minimum duration of 1 minute
    return max(duration_seconds, 60)


def delete_podcast_route(podcast_id):
    """API route to delete a podcast"""
    podcasts = _load_podcasts()

    # Filter out the podcast to delete
    updated_podcasts = [p for p in podcasts if p["id"] != podcast_id]

    # If no podcasts were removed, the ID was not found
    if len(updated_podcasts) == len(podcasts):
        return jsonify({"error": "Podcast not found"}), 404

    # Save updated podcasts list
    _save_podcasts(updated_podcasts)

    return jsonify({"success": True, "message": "Podcast deleted successfully"})


def update_podcast_audio(podcast_id, audio_url):
    """Update a podcast with an audio URL"""
    podcasts = _load_podcasts()

    # Find the podcast by ID
    for podcast in podcasts:
        if podcast["id"] == podcast_id:
            podcast["audioUrl"] = audio_url
            _save_podcasts(podcasts)
            return True

    return False
