import os
import tempfile
from gtts import gTTS
from pydub import AudioSegment
import re

class SimpleTTSGenerator:
    """Handles text-to-speech generation using gTTS (no authentication required)"""
    
    def __init__(self):
        # Available language options for gTTS
        self.available_voices = {
            "en": "English",
            "en-us": "English (US)", 
            "en-uk": "English (UK)",
            "en-au": "English (Australia)",
            "en-ca": "English (Canada)",
            "es": "Spanish",
            "fr": "French",
            "de": "German"
        }
    
    def generate_speech(self, text, output_dir, voice="en", speed=1.0):
        """
        Generate speech from text using gTTS
        
        Args:
            text (str): Text to convert to speech
            output_dir (str): Directory to save the audio file
            voice (str): Language code for TTS
            speed (float): Speed of speech (will be applied via audio processing)
            
        Returns:
            str: Path to the generated audio file
        """
        try:
            # Clean and prepare text
            cleaned_text = self._clean_text_for_tts(text)
            
            if not cleaned_text.strip():
                raise Exception("No valid text found for TTS generation")
            
            # Split text into chunks if too long
            text_chunks = self._split_text_into_chunks(cleaned_text, max_chunk_size=5000)
            
            # Generate audio for each chunk
            audio_segments = []
            
            for i, chunk in enumerate(text_chunks):
                chunk_audio_path = self._generate_chunk_audio(
                    chunk, output_dir, voice, chunk_index=i
                )
                
                # Load audio segment
                audio_segment = AudioSegment.from_mp3(chunk_audio_path)
                audio_segments.append(audio_segment)
                
                # Clean up individual chunk file
                os.remove(chunk_audio_path)
            
            # Combine all audio segments
            if len(audio_segments) == 1:
                final_audio = audio_segments[0]
            else:
                final_audio = audio_segments[0]
                for segment in audio_segments[1:]:
                    # Add small pause between segments
                    pause = AudioSegment.silent(duration=200)  # 200ms pause
                    final_audio = final_audio + pause + segment
            
            # Apply speed adjustment if needed
            if speed != 1.0:
                # Change playback speed
                new_sample_rate = int(final_audio.frame_rate * speed)
                final_audio = final_audio._spawn(final_audio.raw_data, overrides={"frame_rate": new_sample_rate})
                final_audio = final_audio.set_frame_rate(final_audio.frame_rate)
            
            # Save final audio
            final_audio_path = os.path.join(output_dir, "tts_audio.mp3")
            final_audio.export(final_audio_path, format="mp3")
            
            return final_audio_path
            
        except Exception as e:
            raise Exception(f"Failed to generate TTS audio: {str(e)}")
    
    def _generate_chunk_audio(self, text_chunk, output_dir, voice, chunk_index=0):
        """
        Generate audio for a single text chunk using gTTS
        """
        try:
            # Create gTTS object
            tts = gTTS(text=text_chunk, lang=voice, slow=False)
            
            # Save audio chunk
            chunk_path = os.path.join(output_dir, f"tts_chunk_{chunk_index}.mp3")
            tts.save(chunk_path)
            
            return chunk_path
            
        except Exception as e:
            raise Exception(f"Failed to generate audio chunk {chunk_index}: {str(e)}")
    
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
    
    def _split_text_into_chunks(self, text, max_chunk_size=5000):
        """Split text into chunks suitable for gTTS"""
        if len(text) <= max_chunk_size:
            return [text]
        
        chunks = []
        sentences = re.split(r'([.!?]+)', text)
        current_chunk = ""
        
        for i in range(0, len(sentences), 2):
            sentence = sentences[i]
            punctuation = sentences[i + 1] if i + 1 < len(sentences) else ""
            full_sentence = sentence + punctuation
            
            if len(current_chunk) + len(full_sentence) > max_chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = full_sentence
                else:
                    # Single sentence too long, split by words
                    words = sentence.split()
                    word_chunk = ""
                    for word in words:
                        if len(word_chunk) + len(word) + 1 > max_chunk_size:
                            if word_chunk:
                                chunks.append(word_chunk.strip())
                                word_chunk = word
                            else:
                                chunks.append(word[:max_chunk_size])
                        else:
                            word_chunk += " " + word if word_chunk else word
                    if word_chunk:
                        current_chunk = word_chunk + punctuation
            else:
                current_chunk += full_sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks if chunks else [text[:max_chunk_size]]
    
    def get_available_voices(self):
        """Get dictionary of available TTS voices"""
        return self.available_voices.copy()