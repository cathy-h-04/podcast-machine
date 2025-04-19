import azure.cognitiveservices.speech as speechsdk

class TTSClient:
    def __init__(self, subscription_key, region):
        """
        Initialize the Azure Speech SDK client
        
        Args:
            subscription_key (str): Azure Speech API subscription key.
            region (str): Azure region for the Speech resource.
        """
        self.subscription_key = subscription_key
        self.region = region
        self.default_voice = "en-US-MatthewNeural"  # Default voice
        self.supported_voices = {
            "male": ["en-US-MatthewNeural", "en-US-GuyNeural"],
            "female": ["en-US-JennyNeural", "en-US-AriaNeural"]
        }

    def convert_text_to_speech(self, text, voice=None, output_format="mp3"):
        """
        Convert text to speech using Azure Text-to-Speech.
        
        Args:
            text (str): Text to convert to speech.
            voice (str, optional): Voice to use. Defaults to the default voice.
            output_format (str, optional): Audio format. Defaults to "mp3".
        
        Returns:
            bytes: Audio data in the specified format.
        """
        try:
            # Create a speech configuration
            speech_config = speechsdk.SpeechConfig(
                subscription=self.subscription_key, region=self.region
            )
            speech_config.speech_synthesis_voice_name = voice or self.default_voice
            speech_config.set_speech_synthesis_output_format(
                speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3
            )

            # Create a synthesizer
            synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)

            # Synthesize speech
            result = synthesizer.speak_text_async(text).get()

            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                return result.audio_data
            else:
                raise Exception(f"Speech synthesis failed: {result.reason}")
        except Exception as e:
            print(f"Error converting text to speech: {e}")
            raise

    def save_audio(self, audio_data, output_path):
        """
        Save audio data to a file.
        
        Args:
            audio_data (bytes): Audio data to save.
            output_path (str): Path to save the audio file.
        """
        try:
            with open(output_path, "wb") as file:
                file.write(audio_data)
        except Exception as e:
            print(f"Error saving audio file: {e}")
            raise

    def create_conversation(self, script, output_path):
        """
        Create a conversation-style audio from a script.
        
        Args:
            script (list): List of dictionaries containing speaker and text.
                           e.g., [{"speaker": "male1", "text": "Hello"}, ...]
            output_path (str): Path to save the final audio file.
        """
        try:
            audio_segments = []

            for line in script:
                speaker_type = line["speaker"].lower()
                if speaker_type.startswith("male"):
                    voice = self.supported_voices["male"][int(speaker_type[-1]) - 1]
                else:
                    voice = self.supported_voices["female"][int(speaker_type[-1]) - 1]

                audio_data = self.convert_text_to_speech(line["text"], voice)
                audio_segments.append(audio_data)

            # Combine audio segments
            combined_audio = b"".join(audio_segments)
            self.save_audio(combined_audio, output_path)

        except Exception as e:
            print(f"Error creating conversation: {e}")
            raise