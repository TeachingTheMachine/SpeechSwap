import os
import tempfile
import subprocess
import re
import base64

class BasicTTSGenerator:
    """Google Cloud Text-to-Speech generator using Google Cloud TTS API"""
    
    def __init__(self):
        # Check if Google Cloud TTS is available
        try:
            from google.cloud import texttospeech
            self.tts_client = texttospeech.TextToSpeechClient()
            self.google_tts_available = True
            print("Google Cloud TTS initialized successfully")
        except Exception as e:
            self.google_tts_available = False
            print(f"Google Cloud TTS not available: {e}")
        
        # Available Google Cloud TTS voices
        self.available_voices = {
            "en-US-Wavenet-D": "English US (Male, Natural)",
            "en-US-Wavenet-F": "English US (Female, Natural)", 
            "en-GB-Wavenet-A": "English UK (Female, Natural)",
            "en-GB-Wavenet-B": "English UK (Male, Natural)",
            "en-AU-Wavenet-A": "English Australia (Female, Natural)",
            "en-AU-Wavenet-B": "English Australia (Male, Natural)",
            "en-CA-Wavenet-A": "English Canada (Female, Natural)",
            "en-CA-Wavenet-B": "English Canada (Male, Natural)"
        }
    
    def generate_speech(self, text, output_dir, voice="en-US-Wavenet-F", speed=1.0):
        """
        Generate speech from text using Google Cloud TTS API
        
        Args:
            text (str): Text to convert to speech
            output_dir (str): Directory to save the audio file
            voice (str): Voice name from Google Cloud TTS
            speed (float): Speed of speech
            
        Returns:
            str: Path to the generated audio file
        """
        try:
            # Clean and prepare text
            cleaned_text = self._clean_text_for_tts(text)
            
            if not cleaned_text.strip():
                raise Exception("No valid text found for TTS generation")
            
            output_path = os.path.join(output_dir, "tts_audio.mp3")
            
            # Check if Google Cloud TTS is available
            if not self.google_tts_available:
                raise Exception("Google Cloud TTS is not available. Please set up Google Cloud credentials.")
            
            # Use Google Cloud TTS API
            from google.cloud import texttospeech
            
            # Ensure voice is valid
            if voice not in self.available_voices:
                voice = "en-US-Wavenet-F"  # Default to female US English
            
            # Set up synthesis input
            synthesis_input = texttospeech.SynthesisInput(text=cleaned_text)
            
            # Parse voice name to get language and voice name
            language_code = '-'.join(voice.split('-')[:2])  # e.g., "en-US" from "en-US-Wavenet-F"
            voice_name = voice
            
            # Build the voice selection
            voice_selection = texttospeech.VoiceSelectionParams(
                language_code=language_code,
                name=voice_name
            )
            
            # Select the type of audio file to return
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=speed
            )
            
            # Perform the text-to-speech request
            response = self.tts_client.synthesize_speech(
                input=synthesis_input,
                voice=voice_selection,
                audio_config=audio_config
            )
            
            # Write the response to the output file
            with open(output_path, "wb") as out:
                out.write(response.audio_content)
                
            print(f"Google Cloud TTS audio generated successfully: {output_path}")
            return output_path
            
        except Exception as e:
            raise Exception(f"Failed to generate Google Cloud TTS audio: {str(e)}")
    
    
    
    def _clean_text_for_tts(self, text):
        """Clean and prepare text for TTS generation"""
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove excessive whitespace and newlines
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters that might cause issues
        text = re.sub(r'[^\w\s\.,!?;:\-\(\)\"\'\']+', '', text)
        
        # Ensure proper sentence endings
        text = re.sub(r'([.!?])\s*', r'\1 ', text)
        
        return text.strip()
    
    def get_available_voices(self):
        """Get dictionary of available TTS voices"""
        return self.available_voices.copy()