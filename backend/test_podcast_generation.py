#!/usr/bin/env python3
"""
Test script for podcast generation using Cartesia TTS
This script demonstrates the full pipeline of processing a conversation script
and generating a multi-speaker podcast using Cartesia voices.
"""

import os
import sys
from services.script_processor import ScriptProcessor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def generate_podcast_from_script(script_path, output_path):
    """
    Generate a podcast from a script file
    
    Args:
        script_path (str): Path to the script file
        output_path (str): Path to save the podcast audio
    """
    # Check if script file exists
    if not os.path.exists(script_path):
        print(f"Error: Script file not found at {script_path}")
        return False
    
    # Initialize script processor
    try:
        processor = ScriptProcessor()
    except Exception as e:
        print(f"Error initializing script processor: {e}")
        return False
    
    # Override the default voice assignments with more distinct voices
    processor.default_voice_assignments = {
        "Professor Williams": "694f9389-aac1-45b6-b726-9d9369183238",  # Barbershop Man
        "Alex": "a0e99841-438c-4a64-b679-ae501e7d6091",  # Broadcaster Man
    }
    
    # Process the script and generate audio
    print(f"Processing script: {script_path}")
    success = processor.process_script(script_path, output_path)
    
    # Verify the file exists and has content
    if success and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        print(f"Success! Podcast file created with size: {os.path.getsize(output_path) / (1024*1024):.2f} MB")
    else:
        print("Error: Podcast file was not created or is empty.")
    
    if os.path.exists(output_path):
        print(f"Podcast generated successfully: {output_path}")
        # Get file size
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"Podcast file size: {size_mb:.2f} MB")
        return True
    else:
        print("Failed to generate podcast")
        return False

if __name__ == "__main__":
    # Use command line arguments if provided, otherwise use defaults
    if len(sys.argv) > 2:
        script_path = sys.argv[1]
        output_path = sys.argv[2]
    else:
        script_path = "output.txt"
        output_path = "podcast.mp3"
    
    generate_podcast_from_script(script_path, output_path)
