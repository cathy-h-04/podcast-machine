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
    
    # Get list of available audio files
    audio_dir = os.path.join(BASE_DIR, "static", "audio")
    all_files = os.listdir(audio_dir) if os.path.exists(audio_dir) else []
    
    # Filter out system files and non-audio files
    available_files = [f for f in all_files if not f.startswith('.') and f.lower().endswith(('.mp3', '.wav', '.ogg', '.m4a'))]
    print(f"Available audio files: {available_files}")
    
    # If we have audio files but no podcasts with valid audio URLs, create entries for them
    if available_files:
        # Check if we need to create new podcast entries for audio files
        existing_audio_files = set()
        for podcast in podcasts:
            audio_url = podcast.get("audioUrl")
            if audio_url and audio_url.startswith("/static/audio/"):
                audio_filename = audio_url.split("/")[-1]
                base_name = os.path.splitext(audio_filename)[0]
                # Add both the exact filename and the base name to our set
                existing_audio_files.add(audio_filename)
                existing_audio_files.add(base_name)
        
        # Create podcasts for audio files that don't have entries
        for audio_file in available_files:
            base_name = os.path.splitext(audio_file)[0]
            # If neither the exact filename nor the base name exists in any podcast
            if audio_file not in existing_audio_files and base_name not in existing_audio_files:
                # Create a new podcast entry
                new_podcast = {
                    "id": str(uuid.uuid4()),
                    "title": f"Audio {base_name}",
                    "format": "podcast",  # Default format
                    "createdAt": datetime.now().isoformat(),
                    "duration": 300,  # Default duration (5 minutes)
                    "audioUrl": f"/static/audio/{audio_file}",
                    "cover_url": None,
                    "listened": False
                }
                podcasts.append(new_podcast)
                print(f"Created new podcast entry for audio file: {audio_file}")
    
    # Update existing podcasts to point to valid audio files
    for podcast in podcasts:
        audio_url = podcast.get("audioUrl")
        if not audio_url or audio_url == "#":
            continue
            
        if audio_url.startswith("/static/audio/"):
            audio_filename = audio_url.split("/")[-1]
            audio_path = os.path.join(BASE_DIR, "static", "audio", audio_filename)
            
            # If the exact file doesn't exist, try to find a matching file
            if not os.path.exists(audio_path):
                base_name = os.path.splitext(audio_filename)[0]
                matching_files = [f for f in available_files if f.startswith(base_name)]
                
                if matching_files:
                    # Update to the first matching file
                    podcast["audioUrl"] = f"/static/audio/{matching_files[0]}"
                    print(f"Updated podcast audio URL to: {podcast['audioUrl']}")
    
    # Save any updates we made to the podcasts
    _save_podcasts(podcasts)
    
    # Filter out podcasts with invalid audio files (like .DS_Store)
    valid_podcasts = []
    for podcast in podcasts:
        audio_url = podcast.get("audioUrl")
        if audio_url and audio_url.startswith("/static/audio/"):
            filename = audio_url.split("/")[-1]
            # Only include podcasts with valid audio file extensions
            if not filename.startswith('.') and any(filename.lower().endswith(ext) for ext in ('.mp3', '.wav', '.ogg', '.m4a')):
                valid_podcasts.append(podcast)
        else:
            # Keep podcasts with external URLs
            valid_podcasts.append(podcast)
    
    # Save the filtered podcasts list
    _save_podcasts(valid_podcasts)
    
    return jsonify({"podcasts": valid_podcasts})


def get_podcast_route(podcast_id):
    """API route to get a specific podcast by ID"""
    podcasts = _load_podcasts()
    podcast = next((p for p in podcasts if p["id"] == podcast_id), None)

    if not podcast:
        return jsonify({"error": "Podcast not found"}), 404

    return jsonify({"podcast": podcast})


def save_podcast(title, format, script, audio_url=None):
    """Save a new podcast to the database"""
    podcasts = _load_podcasts()

    # Create a new podcast entry
    new_podcast = {
        "id": str(uuid.uuid4()),
        "title": title,
        "format": format.lower(),  # podcast, debate, or duck
        "createdAt": datetime.now().isoformat(),
        "duration": calculate_duration(script),  # Calculate based on script length
        "audioUrl": audio_url or "#",  # Placeholder if no audio URL yet
        "cover_url": None,  # Placeholder for cover art URL
        "listened": False,
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
    podcast = next((p for p in podcasts if p["id"] == podcast_id), None)

    if not podcast:
        return None

    # Update the audio URL
    podcast["audioUrl"] = audio_url
    _save_podcasts(podcasts)

    return podcast


def update_podcast_cover(podcast_id, cover_url):
    """Update a podcast with a cover art URL"""
    podcasts = _load_podcasts()
    podcast = next((p for p in podcasts if p["id"] == podcast_id), None)

    if not podcast:
        return None

    # Update the cover URL
    podcast["cover_url"] = cover_url
    _save_podcasts(podcasts)

    return podcast


def update_podcast_title(podcast_id, new_title):
    """Update a podcast's title"""
    podcasts = _load_podcasts()
    podcast = next((p for p in podcasts if p["id"] == podcast_id), None)

    if not podcast:
        return None

    # Update the title
    podcast["title"] = new_title
    _save_podcasts(podcasts)

    return podcast


def toggle_podcast_listened(podcast_id):
    """Toggle the listened status of a podcast"""
    podcasts = _load_podcasts()
    podcast = next((p for p in podcasts if p["id"] == podcast_id), None)

    if not podcast:
        return None

    # If the podcast doesn't have a listened field yet, add it
    if "listened" not in podcast:
        podcast["listened"] = False

    # Toggle the listened status
    podcast["listened"] = not podcast["listened"]
    _save_podcasts(podcasts)

    return podcast
