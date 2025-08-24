import os
import tempfile
import subprocess
import re

class BasicTTSGenerator:
    """Google Text-to-Speech generator using gTTS"""
    
    def __init__(self):
        # Check if gTTS is available
        try:
            from gtts import gTTS
            self.gtts_available = True
        except ImportError:
            self.gtts_available = False
            print("Warning: gTTS package not available. Please install it for Google TTS functionality.")
        
        # Available Google TTS voices
        self.available_voices = {
            "en": "English (US)",
            "en-us": "English (US)", 
            "en-uk": "English (UK)",
            "en-au": "English (Australia)",
            "en-ca": "English (Canada)",
            "en-in": "English (India)"
        }
    
    def generate_speech(self, text, output_dir, voice="en", speed=1.0):
        """
        Generate speech from text using Google TTS
        
        Args:
            text (str): Text to convert to speech
            output_dir (str): Directory to save the audio file
            voice (str): Voice language code
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
            
            # Check if gTTS is available
            if not self.gtts_available:
                raise Exception("gTTS package is not available. Please install it to use Google TTS.")
            
            # Import gTTS here after checking availability
            from gtts import gTTS
            
            # Use Google TTS
            lang_code = voice.split('-')[0]  # Extract language code (e.g., 'en' from 'en-us')
            slow_speech = speed < 0.8
            
            # Create gTTS object and generate speech
            tts = gTTS(text=cleaned_text, lang=lang_code, slow=slow_speech)
            tts.save(output_path)
            
            # Apply speed adjustment if needed
            if speed != 1.0 and speed >= 0.8:
                self._adjust_audio_speed(output_path, speed)
            
            return output_path
            
        except Exception as e:
            raise Exception(f"Failed to generate Google TTS audio: {str(e)}")
    
    def _adjust_audio_speed(self, audio_path, speed):
        """Adjust audio speed using ffmpeg"""
        try:
            temp_path = audio_path.replace('.mp3', '_temp.mp3')
            
            cmd = [
                'ffmpeg', '-y',
                '-i', audio_path,
                '-filter:a', f'atempo={speed}',
                temp_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                os.replace(temp_path, audio_path)
            else:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    
        except Exception as e:
            print(f"Speed adjustment failed: {e}")
    
    
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