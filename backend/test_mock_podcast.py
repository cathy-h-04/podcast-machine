#!/usr/bin/env python3
"""
Test script for podcast generation with mocked audio
This script demonstrates the podcast generation pipeline without making actual API calls
"""

import os
import sys
import tempfile
from services.script_processor import ScriptProcessor

class MockScriptProcessor(ScriptProcessor):
    """
    A mock version of ScriptProcessor that doesn't make actual API calls
    """
    
    def generate_audio_segments(self, conversation, output_dir):
        """
        Mock implementation that creates dummy WAV files instead of calling Cartesia
        """
        print(f"Generating mock audio for {len(conversation)} segments")
        segment_paths = []
        
        # Create a simple WAV header (44 bytes) for a silent mono 44.1kHz 16-bit PCM file
        wav_header = bytes.fromhex(
            '52494646'  # "RIFF"
            '24000000'  # Chunk size (36 + data size)
            '57415645'  # "WAVE"
            '666d7420'  # "fmt "
            '10000000'  # Subchunk1 size (16 bytes)
            '0100'      # Audio format (1 = PCM)
            '0100'      # Num channels (1 = mono)
            '44AC0000'  # Sample rate (44100 Hz)
            '88580100'  # Byte rate (44100 * 2)
            '0200'      # Block align (2 bytes)
            '1000'      # Bits per sample (16)
            '64617461'  # "data"
            '00000000'  # Subchunk2 size (0 bytes of actual audio data)
        )
        
        # Add 1 second of silence (44100 samples * 2 bytes per sample)
        silence_1sec = bytes(44100 * 2)
        
        for i, item in enumerate(conversation):
            speaker = item["speaker"]
            text = item["text"]
            
            # Get voice ID for this speaker
            voice_id = self.speaker_voice_mapping.get(speaker)
            if not voice_id and self.available_voices:
                voice_id = self.available_voices[0]["id"]
            
            # Create a mock WAV file with the header and some silence
            # Length of silence proportional to text length (rough approximation)
            silence_duration = min(5, max(1, len(text) // 50))  # Between 1-5 seconds
            silence_data = silence_1sec * silence_duration
            
            # Update WAV header with correct data size
            data_size = len(silence_data)
            chunk_size = 36 + data_size
            wav_data = bytearray(wav_header)
            wav_data[4:8] = chunk_size.to_bytes(4, byteorder='little')
            wav_data[40:44] = data_size.to_bytes(4, byteorder='little')
            
            # Save to file
            segment_path = os.path.join(output_dir, f"segment_{i:03d}.wav")
            with open(segment_path, "wb") as f:
                f.write(wav_data)
                f.write(silence_data)
            
            segment_paths.append(segment_path)
            print(f"Generated mock segment {i+1}/{len(conversation)} for {speaker}")
        
        return segment_paths

def main():
    # Check if the script file is provided as an argument
    if len(sys.argv) > 1:
        script_file = sys.argv[1]
    else:
        script_file = "output.txt"  # Default script file
    
    # Create a MockScriptProcessor instance
    processor = MockScriptProcessor()
    
    # Process the script
    print(f"Processing script: {script_file}")
    output_path = "mock_podcast.wav"
    processor.process_script(script_file, output_path)
    
    # Check if the podcast was generated successfully
    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        print(f"Mock podcast generated successfully: {output_path}")
        print(f"File size: {os.path.getsize(output_path) / 1024:.2f} KB")
    else:
        print("Error: Mock podcast file was not created or is empty.")
        sys.exit(1)

if __name__ == "__main__":
    main()
