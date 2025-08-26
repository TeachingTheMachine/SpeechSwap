import os
import tempfile
import subprocess
import re
from openai import OpenAI

class BasicTTSGenerator:
    """OpenAI Text-to-Speech generator using OpenAI TTS API"""
    
    def __init__(self):
        # Initialize OpenAI client
        try:
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise Exception("OPENAI_API_KEY environment variable not found")
            
            self.openai_client = OpenAI(api_key=api_key)
            self.openai_tts_available = True
            print("OpenAI TTS initialized successfully")
        except Exception as e:
            self.openai_tts_available = False
            print(f"OpenAI TTS not available: {e}")
        
        # Available OpenAI TTS voices
        self.available_voices = {
            "alloy": "Alloy (Balanced, Versatile)",
            "echo": "Echo (Male, Clear)", 
            "fable": "Fable (Expressive, Warm)",
            "onyx": "Onyx (Male, Deep)",
            "nova": "Nova (Female, Bright)",
            "shimmer": "Shimmer (Female, Soft)"
        }
    
    def generate_speech(self, text, output_dir, voice="nova", speed=1.0, target_duration=None):
        """
        Generate speech from text using OpenAI TTS API
        
        Args:
            text (str): Text to convert to speech
            output_dir (str): Directory to save the audio file
            voice (str): Voice name from OpenAI TTS
            speed (float): Speed of speech (0.25 to 4.0)
            target_duration (float): Target duration in seconds for automatic speed adjustment
            
        Returns:
            str: Path to the generated audio file
        """
        try:
            # Clean and prepare text
            cleaned_text = self._clean_text_for_tts(text)
            
            if not cleaned_text.strip():
                raise Exception("No valid text found for TTS generation")
            
            output_path = os.path.join(output_dir, "tts_audio.mp3")
            
            # Check if OpenAI TTS is available
            if not self.openai_tts_available:
                raise Exception("OpenAI TTS is not available. Please check your API key.")
            
            # Ensure voice is valid
            if voice not in self.available_voices:
                voice = "nova"  # Default to Nova voice
            
            # Auto-adjust speed if target duration is provided
            if target_duration:
                # Estimate words per minute for the voice (approximate)
                estimated_wpm = 150  # Average speaking rate
                word_count = len(cleaned_text.split())
                estimated_duration = (word_count / estimated_wpm) * 60
                
                if estimated_duration > 0:
                    suggested_speed = estimated_duration / target_duration
                    # Only use auto-adjustment if it's within reasonable bounds
                    if 0.25 <= suggested_speed <= 4.0:
                        speed = suggested_speed
                        print(f"Auto-adjusted speed to {speed:.2f} for target duration {target_duration}s")
            
            # Clamp speed to valid range for OpenAI TTS
            speed = max(0.25, min(4.0, speed))
            
            # Use OpenAI TTS API
            response = self.openai_client.audio.speech.create(
                model="tts-1",  # Use tts-1 model for faster generation
                voice=voice,
                input=cleaned_text,
                speed=speed
            )
            
            # Write the response to the output file
            with open(output_path, "wb") as f:
                for chunk in response.iter_bytes():
                    f.write(chunk)
                
            print(f"OpenAI TTS audio generated successfully: {output_path}")
            return output_path
            
        except Exception as e:
            raise Exception(f"Failed to generate OpenAI TTS audio: {str(e)}")
    
        
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