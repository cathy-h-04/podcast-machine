"""
Script Processor for Podcast Generation
--------------------------------------
Processes conversation scripts and generates audio using Cartesia TTS.
Handles multi-speaker conversations with different voices for each speaker.
"""

import os
import json
import subprocess
import tempfile
import time
import uuid
import shutil
import re
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional

import dotenv
from cartesia import Cartesia

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ScriptProcessor')

# Load environment variables
dotenv.load_dotenv()

class ScriptProcessor:
    def __init__(self, api_key=None):
        """
        Initialize the script processor
        
        Args:
            api_key (str, optional): Cartesia API key. If not provided, will attempt to load from environment variables.
        """
        # Initialize Cartesia client
        cartesia_api_key = os.getenv("CARTESIA_API_KEY")
        if not cartesia_api_key:
            raise ValueError("CARTESIA_API_KEY environment variable is required")
        self.client = Cartesia(api_key=cartesia_api_key)
        
        # Available voices with distinct characteristics - using valid Cartesia voice IDs
        self.available_voices = [
            # Male voices - using IDs without the cartesia. prefix
            {"id": "694f9389-aac1-45b6-b726-9d9369183238", "gender": "male", "type": "Sarah"},
            {"id": "a0e99841-438c-4a64-b679-ae501e7d6091", "gender": "male", "type": "Barbershop Man"},
            {"id": "d46abd1d-2d02-43e8-819f-51fb652c1c61", "gender": "male", "type": "Newsman"},
            {"id": "f146dcec-e481-45be-8ad2-96e1e40e7f32", "gender": "male", "type": "Reading Man"},
            {"id": "34575e71-908f-4ab6-ab54-b08c95d6597d", "gender": "male", "type": "New York Man"},
            
            # Female voices - using IDs without the cartesia. prefix
            {"id": "bf991597-6c13-47e4-8411-91ec2de5c466", "gender": "female", "type": "Newslady"},
            {"id": "00a77add-48d5-4ef6-8157-71e5437b282d", "gender": "female", "type": "Calm Lady"},
            {"id": "156fb8d2-335b-4950-9cb3-a2d33befec77", "gender": "female", "type": "Helpful Woman"},
            {"id": "b7d50908-b17c-442d-ad8d-810c63997ed9", "gender": "female", "type": "California Girl"},
            {"id": "71a7ad14-091c-4e8e-a314-022ece01c121", "gender": "female", "type": "British Reading Lady"},
        ]
        
        # This will be populated dynamically based on detected speakers
        self.speaker_voice_mapping = {}
    
    def detect_speakers_and_assign_voices(self, conversation):
        """
        Detect unique speakers in the conversation and assign distinct voices to them
        
        Args:
            conversation (list): List of dictionaries with speaker and text
            
        Returns:
            dict: Mapping of speaker names to voice IDs
        """
        # Extract unique speakers
        unique_speakers = set(item["speaker"] for item in conversation)
        logger.info(f"Detected {len(unique_speakers)} unique speakers: {', '.join(unique_speakers)}")
        
        # Reset speaker voice mapping
        self.speaker_voice_mapping = {}
        
        # Assign voices to ensure maximum distinction
        if len(unique_speakers) == 1:
            # If only one speaker, use a default voice
            speaker = list(unique_speakers)[0]
            self.speaker_voice_mapping[speaker] = self.available_voices[0]["id"]
        
        elif len(unique_speakers) == 2:
            # For two speakers, use one male and one female voice for maximum distinction
            speakers = list(unique_speakers)
            self.speaker_voice_mapping[speakers[0]] = self.available_voices[0]["id"]  # Male voice
            self.speaker_voice_mapping[speakers[1]] = self.available_voices[5]["id"]  # Female voice
        
        else:
            # For more speakers, distribute available voices
            speakers = list(unique_speakers)
            for i, speaker in enumerate(speakers):
                voice_index = i % len(self.available_voices)
                self.speaker_voice_mapping[speaker] = self.available_voices[voice_index]["id"]
        
        logger.info("Voice assignments:")
        for speaker, voice_id in self.speaker_voice_mapping.items():
            voice_info = next((v for v in self.available_voices if v["id"] == voice_id), None)
            if voice_info:
                logger.info(f"  {speaker}: {voice_info['gender']} {voice_info['type']}")
            else:
                logger.info(f"  {speaker}: {voice_id}")
        
        return self.speaker_voice_mapping
    
    def parse_script(self, script_path):
        """
        Parse a script file into a list of speaker-text pairs
        
        Args:
            script_path (str): Path to the script file
            
        Returns:
            list: List of dictionaries with speaker and text
                 [{"speaker": "Host", "text": "Hello"}, ...]
        """
        try:
            logger.info(f"Parsing script file: {script_path}")
            # Read the script file
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple approach: Skip everything before the closing metadata tag
            # Look for closing tags like </END_OF_METADATA_TAG>, </script_planning>, etc.
            closing_tag_match = re.search(r'</[^>]+>', content)
            if closing_tag_match:
                # Skip everything before and including the closing tag
                content = content[closing_tag_match.end():].strip()
                logger.info("Skipped metadata before closing tag")
            
            # Find the first actual dialogue line (with speaker pattern)
            lines = content.split('\n')
            start_idx = 0
            for i, line in enumerate(lines):
                # Look for speaker pattern: [Speaker]: or Speaker:
                if re.search(r'^\[.*?\]:|^[^\[\]]+:', line.strip()):
                    start_idx = i
                    break
            
            # Skip everything before the first dialogue line
            if start_idx > 0:
                content = '\n'.join(lines[start_idx:])
                logger.info(f"Skipped {start_idx} non-dialogue lines at the beginning")
        except Exception as e:
            logger.error(f"Error reading script file: {e}")
            return []
        
        # Parse the conversation
        lines = content.split('\n')
        conversation = []
        current_speaker = None
        current_text = []
        
        for line in lines:
            line = line.strip()
            if not line:
                # Empty line - if we have a current speaker, add their text
                if current_speaker and current_text:
                    conversation.append({
                        "speaker": current_speaker,
                        "text": ' '.join(current_text)
                    })
                    current_text = []
                continue
            
            # Skip lines that look like metadata or planning notes
            if line.startswith('#') or line.startswith('//') or line.startswith('/*'):
                continue
                
            # Check if this is a new speaker line
            # Match both [Speaker]: format and Speaker: format
            speaker_match = re.match(r'^\[(.*?)\]:\s*(.*)|^([^\[\]]+):\s*(.*)', line)
            if speaker_match:
                # If we have a previous speaker, add their text
                if current_speaker and current_text:
                    conversation.append({
                        "speaker": current_speaker,
                        "text": ' '.join(current_text)
                    })
                
                # Start new speaker
                # Handle both [Speaker]: format and Speaker: format
                if speaker_match.group(1) is not None:  # [Speaker]: format
                    current_speaker = speaker_match.group(1).strip()
                    text_part = speaker_match.group(2).strip()
                else:  # Speaker: format
                    current_speaker = speaker_match.group(3).strip()
                    text_part = speaker_match.group(4).strip()
                
                # Skip metadata-like speakers or lines that are likely metadata
                metadata_keywords = ['title', 'guest', 'tone', 'length', 'format', 'topic', 'desired', 'include', 'conversational']
                if (any(keyword in current_speaker.lower() for keyword in metadata_keywords) or 
                    len(current_speaker) > 30):  # Overly long speaker names are likely metadata
                    current_speaker = None
                    current_text = []
                    continue
                    
                current_text = [text_part] if text_part else []
            else:
                # Continue with current speaker
                if current_speaker:
                    current_text.append(line)
        
        # Add the last speaker's text if any
        if current_speaker and current_text:
            conversation.append({
                "speaker": current_speaker,
                "text": ' '.join(current_text)
            })
        
        logger.info(f"Parsed script with {len(conversation)} dialogue lines")
        return conversation
    
    def assign_voices(self, conversation):
        """
        Assign appropriate voices to each speaker in the conversation
        
        Args:
            conversation (list): List of speaker-text pairs
            
        Returns:
            dict: Mapping of speakers to voice IDs
        """
        # Extract unique speakers
        speakers = set(item["speaker"].lower() for item in conversation)
        
        # Assign voices based on speaker names or roles
        voice_assignments = {}
        male_count = 1
        for speaker in speakers:
            speaker_lower = speaker.lower()
            
            # Check if speaker matches any default mapping
            # Get voice ID for this speaker from our dynamic mapping
            voice_id = self.speaker_voice_mapping.get(speaker)
            
            # If no voice assigned yet (shouldn't happen), use a default
            if not voice_id and self.available_voices:
                voice_id = self.available_voices[0]["id"]
            
            voice_assignments[speaker] = voice_id
        
        return voice_assignments
    
    def generate_audio_segments(self, conversation, output_dir):
        """
        Generate audio segments for each part of the conversation
        
        Args:
            conversation (list): List of speaker-text pairs
            output_dir (str): Directory to save audio segments
            
        Returns:
            list: List of paths to audio segments in order
        """
        os.makedirs(output_dir, exist_ok=True)
        segment_paths = []
        
        try:
            logger.info(f"Generating audio segments for {len(conversation)} dialogue lines")
            for i, item in enumerate(conversation):
                speaker = item["speaker"]
                text = item["text"]
                
                # Get voice ID for this speaker
                voice_id = self.speaker_voice_mapping.get(speaker, self.available_voices[0]["id"])
                
                # Configure output format for raw audio (SSE endpoint only supports raw)
                format_config = {
                    "container": "raw",
                    "sample_rate": 44100,
                    "encoding": "pcm_f32le",
                }
                
                try:
                    # Get WAV audio data directly from Cartesia
                    logger.info(f"Generating audio for {speaker}: '{text[:50]}{'...' if len(text) > 50 else ''}' using voice {voice_id}")
                    
                    # Configure output format for bytes endpoint
                    format_config = {
                        "container": "wav",
                        "sample_rate": 44100,
                        "encoding": "pcm_f32le",
                    }
                    
                    # Generate audio using Cartesia's bytes API
                    response = self.client.tts.bytes(
                        model_id="sonic-2",
                        transcript=text,
                        voice={
                            "mode": "id",
                            "id": voice_id
                        },
                        output_format=format_config
                    )
                    
                    # Handle response which might be a generator
                    if hasattr(response, '__iter__') and not isinstance(response, bytes):
                        # It's a generator, collect all chunks
                        audio_chunks = []
                        for chunk in response:
                            if hasattr(chunk, 'data') and chunk.data is not None:
                                audio_chunks.append(chunk.data)
                            elif isinstance(chunk, bytes):
                                audio_chunks.append(chunk)
                        audio_data = b''.join(audio_chunks)
                    else:
                        # It's already bytes
                        audio_data = response
                    
                    # Save audio data to WAV file
                    segment_path = os.path.join(output_dir, f"segment_{i:03d}.wav")
                    with open(segment_path, "wb") as f:
                        f.write(audio_data)
                    
                    segment_paths.append(segment_path)
                    logger.info(f"Generated segment {i+1}/{len(conversation)}")
                    
                except Exception as e:
                    error_message = str(e)
                    logger.error(f"Error generating audio for segment {i}: {e}")
                    
                    # If we hit the credit limit, let's stop trying to generate more segments
                    if "credit limit reached" in error_message.lower():
                        logger.info("Cartesia API credit limit reached. Will create podcast with segments generated so far.")
                        break
                        
                    # Create an empty file as placeholder to maintain order
                    segment_path = os.path.join(output_dir, f"segment_{i:03d}.mp3")
                    with open(segment_path, "wb") as f:
                        f.write(b"")
                    segment_paths.append(segment_path)
        except Exception as e:
            logger.error(f"Error generating audio segments: {e}")
            # Create an empty file as placeholder to maintain order
            segment_path = os.path.join(output_dir, f"segment_{len(segment_paths):03d}.mp3")
            with open(segment_path, "wb") as f:
                f.write(b"")
            segment_paths.append(segment_path)
        return segment_paths
    
    def combine_audio_segments(self, segment_paths, output_path):
        """
        Combine audio segments into a single file
        
        Args:
            segment_paths (list): List of paths to audio segments
            output_path (str): Path to output file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create a file list for ffmpeg - only include WAV files
            valid_segments = []
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
                file_list = f.name
                for segment_path in segment_paths:
                    if os.path.exists(segment_path) and os.path.getsize(segment_path) > 0 and segment_path.endswith(".wav"):
                        f.write(f"file '{os.path.abspath(segment_path)}'\n")
                        valid_segments.append(segment_path)
                    else:
                        logger.warning(f"Skipping empty or missing file: {segment_path}")
            
            logger.info(f"Including {len(valid_segments)} valid audio segments in the podcast")
            
            # If we have no valid segments, return False
            if not valid_segments:
                logger.error("No valid audio segments found. Cannot create podcast.")
                return False
            
            # Ensure output path has .wav extension
            if not output_path.lower().endswith('.wav'):
                base_path = os.path.splitext(output_path)[0]
                output_path = f"{base_path}.wav"
            
            # Concatenate files with ffmpeg - using pcm_f32le codec for WAV files
            subprocess.run([
                'ffmpeg', '-y', '-f', 'concat', '-safe', '0', 
                '-i', file_list, '-c:a', 'pcm_s16le', '-ar', '44100', output_path
            ], check=True)
            
            # Clean up temporary file
            os.unlink(file_list)
            
            # Check if the output file was created successfully
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                logger.info(f"Podcast generated successfully: {output_path}")
                logger.info(f"Podcast file size: {os.path.getsize(output_path) / (1024 * 1024):.2f} MB")
                return True
            else:
                logger.error(f"Output file {output_path} was not created or is empty")
                return False
        except Exception as e:
            logger.exception(f"Error combining audio segments: {e}")
            return False
    
    def process_script(self, script_path, output_path, callback=None):
        """
        Process a script file and generate a podcast
        
        Args:
            script_path (str): Path to the script file
            output_path (str): Path to save the podcast
            callback (function, optional): Callback function to report progress
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Report progress: Starting script processing
            logger.info(f"Starting script processing: {script_path}")
            if callback:
                callback({"status": "processing", "step": "parsing", "progress": 10, 
                         "message": "Parsing script file"})
            
            # Parse the script
            conversation = self.parse_script(script_path)
            if not conversation:
                logger.error("Failed to parse script")
                if callback:
                    callback({"status": "error", "step": "parsing", "progress": 10, 
                             "message": "Failed to parse script"})
                return False
            
            logger.info(f"Successfully parsed script with {len(conversation)} dialogue lines")
            if callback:
                callback({"status": "processing", "step": "speaker_detection", "progress": 30, 
                         "message": "Detecting speakers and assigning voices"})
            
            # Detect speakers and assign voices
            self.detect_speakers_and_assign_voices(conversation)
            
            # Report progress: Generating audio segments
            logger.info("Starting audio segment generation")
            if callback:
                callback({"status": "processing", "step": "audio_generation", "progress": 50, 
                         "message": "Generating audio segments"})
            
            # Generate audio segments
            output_dir = tempfile.mkdtemp()
            segment_paths = self.generate_audio_segments(conversation, output_dir)
            
            # Report progress: Combining audio segments
            logger.info(f"Generated {len(segment_paths)} audio segments, now combining")
            if callback:
                callback({"status": "processing", "step": "combining", "progress": 80, 
                         "message": "Combining audio segments"})
            
            # Combine audio segments
            success = self.combine_audio_segments(segment_paths, output_path)
            
            # Clean up temporary directory
            shutil.rmtree(output_dir, ignore_errors=True)
            
            # Report final status
            if success:
                logger.info(f"Successfully generated podcast: {output_path}")
                if callback:
                    callback({"status": "complete", "step": "finished", "progress": 100, 
                             "message": "Podcast generation complete"})
            else:
                logger.error("Failed to generate podcast")
                if callback:
                    callback({"status": "error", "step": "combining", "progress": 80, 
                             "message": "Failed to combine audio segments"})
            
            return success
        except Exception as e:
            logger.exception(f"Error processing script: {e}")
            if callback:
                callback({"status": "error", "step": "processing", "progress": 0, 
                         "message": f"Error: {str(e)}"})
            return False


# Example usage
if __name__ == "__main__":
    processor = ScriptProcessor()
    script_path = "output.txt"
    output_path = "podcast.mp3"
    
    success = processor.process_script(script_path, output_path)
    
    if success:
        print(f"Podcast generated successfully: {output_path}")
    else:
        print("Failed to generate podcast")
