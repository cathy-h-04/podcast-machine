#!/usr/bin/env python3
import os
import json
import glob

# Path to podcasts data file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PODCASTS_DATA_PATH = os.path.join(BASE_DIR, "data", "podcasts.json")
AUDIO_DIR = os.path.join(BASE_DIR, "static", "audio")

def update_audio_extensions():
    """Update all podcast audio URLs from .mp3 to .wav and create dummy .wav files if needed"""
    try:
        # Check if the podcasts file exists
        if not os.path.exists(PODCASTS_DATA_PATH):
            print(f"Podcasts file not found at {PODCASTS_DATA_PATH}")
            return
        
        # Load the podcasts data
        with open(PODCASTS_DATA_PATH, "r") as f:
            data = json.load(f)
        
        podcasts = data.get("podcasts", [])
        updated_count = 0
        
        # Update each podcast's audio URL
        for podcast in podcasts:
            audio_url = podcast.get("audioUrl")
            if audio_url and audio_url.endswith(".mp3"):
                # Get the filename from the URL
                old_filename = os.path.basename(audio_url)
                new_filename = old_filename.replace(".mp3", ".wav")
                
                # Update the URL in the database
                new_url = audio_url.replace(".mp3", ".wav")
                podcast["audioUrl"] = new_url
                updated_count += 1
                
                print(f"Updated URL from {audio_url} to {new_url}")
                
                # Check if the .wav file exists, if not create a dummy file
                wav_path = os.path.join(AUDIO_DIR, new_filename)
                if not os.path.exists(wav_path):
                    print(f"Creating dummy .wav file at {wav_path}")
                    # Create a simple 1KB dummy file
                    with open(wav_path, "wb") as f:
                        f.write(b"\x00" * 1024)
        
        # Save the updated data
        data["podcasts"] = podcasts
        with open(PODCASTS_DATA_PATH, "w") as f:
            json.dump(data, f, indent=2)
        
        print(f"Updated {updated_count} podcast audio URLs from .mp3 to .wav")
    
    except Exception as e:
        print(f"Error updating podcast audio URLs: {str(e)}")

if __name__ == "__main__":
    update_audio_extensions()
