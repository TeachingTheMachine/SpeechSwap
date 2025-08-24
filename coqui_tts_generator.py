"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                            coqui_tts_generator.py                            ║
║                                                                              ║
║  Author: Claude                                                              ║
║  Date Created: August 23, 2025                                              ║
║  File Purpose: Coqui TTS integration for high-quality offline TTS            ║
║  Date Modified: August 23, 2025                                             ║
║  Mod Purpose: Initial implementation of Coqui TTS for YouTube voice project  ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import tempfile
import re
from pydub import AudioSegment
import streamlit as st
import subprocess
import numpy as np

class CoquiTTSGenerator:
    """Handles text-to-speech generation using Coqui TTS (offline, high-quality)"""

    def __init__(self):
        # Install required packages if not already installed
        self._ensure_dependencies()

        # Initialize TTS engine
        from TTS.api import TTS

        # Available voice models
        self.available_voices = {
            "en_female": "English (Female, High Quality)",
            "en_male": "English (Male, High Quality)", 
            "en_multi": "English (Multi-Speaker)",
            "en_fast": "English (Fast Mode)",
            "en_emotional": "English (Emotional)",
        }

        # Map voice names to actual model names
        self.voice_models = {
            "en_female": "tts_models/en/ljspeech/tacotron2-DDC",
            "en_male": "tts_models/en/vctk/vits",
            "en_multi": "tts_models/en/vctk/vits",
            "en_fast": "tts_models/en/ljspeech/fast_pitch",
            "en_emotional": "tts_models/en/ljspeech/glow-tts",
        }

        # Map voice names to speaker IDs (for multi-speaker models)
        self.voice_speaker_map = {
            "en_male": "p326",  # VCTK male speaker
            "en_multi": "p225",  # VCTK female speaker
        }

        try:
            # Initialize with default model - will be changed as needed
            self.tts = TTS(model_name=self.voice_models["en_female"], progress_bar=False)
            st.success("✅ Coqui TTS initialized successfully!")
        except Exception as e:
            raise Exception(f"Failed to initialize Coqui TTS: {str(e)}")

    def _ensure_dependencies(self):
        """Ensure all required dependencies are installed"""
        try:
            # Try importing TTS to check if installed
            import importlib
            tts_spec = importlib.util.find_spec("TTS")

            if tts_spec is None:
                st.warning("⚠️ Installing Coqui TTS... This may take a moment.")
                subprocess.check_call(["pip", "install", "TTS"])
                st.success("✅ Coqui TTS installed successfully!")
        except Exception as e:
            raise Exception(f"Failed to install Coqui TTS: {str(e)}")

    def generate_speech(self, text, output_dir, voice="en_female", speed=1.0):
        """
        Generate speech from text using Coqui TTS

        Args:
            text (str): Text to convert to speech
            output_dir (str): Directory to save the audio file
            voice (str): Voice to use for TTS
            speed (float): Speed of speech (0.5 to 2.0)

        Returns:
            str: Path to the generated audio file
        """
        try:
            # Validate inputs
            if voice not in self.available_voices:
                voice = "en_female"  # Default fallback

            speed = max(0.5, min(2.0, speed))  # Clamp speed to valid range

            # Clean and prepare text
            cleaned_text = self._clean_text_for_tts(text)

            if not cleaned_text.strip():
                raise Exception("No valid text found for TTS generation")

            # Split text into chunks if too long (Coqui can struggle with very long texts)
            text_chunks = self._split_text_into_chunks(cleaned_text, max_chunk_size=500)

            # Determine if we need to load a different model
            model_name = self.voice_models[voice]
            current_model = self.tts.model_name

            if current_model != model_name:
                from TTS.api import TTS
                st.info(f"🔄 Loading voice model: {voice}")
                self.tts = TTS(model_name=model_name, progress_bar=False)

            # Generate audio for each chunk
            audio_segments = []

            for i, chunk in enumerate(text_chunks):
                # Create a temporary file for this chunk
                chunk_path = os.path.join(output_dir, f"tts_chunk_{i}.wav")

                # Generate speech for this chunk
                if voice in self.voice_speaker_map and hasattr(self.tts, "speakers"):
                    # Multi-speaker model
                    speaker = self.voice_speaker_map[voice]
                    self.tts.tts_to_file(text=chunk, file_path=chunk_path, speaker=speaker)
                else:
                    # Single-speaker model
                    self.tts.tts_to_file(text=chunk, file_path=chunk_path)

                # Load audio segment
                audio_segment = AudioSegment.from_file(chunk_path)
                audio_segments.append(audio_segment)

                # Clean up individual chunk file
                os.remove(chunk_path)

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
                # Method 1: Change sample rate (simpler but affects pitch)
                if speed >= 0.9 and speed <= 1.1:
                    # For small adjustments, use sample rate change for better quality
                    new_sample_rate = int(final_audio.frame_rate * speed)
                    final_audio = final_audio._spawn(final_audio.raw_data, overrides={"frame_rate": new_sample_rate})
                    final_audio = final_audio.set_frame_rate(final_audio.frame_rate)
                else:
                    # For larger adjustments, use FFmpeg
                    temp_path = os.path.join(output_dir, "temp_audio.wav")
                    final_audio.export(temp_path, format="wav")

                    # Use FFmpeg for better time stretching
                    output_temp = os.path.join(output_dir, "temp_stretched.wav")

                    # Handle extreme speeds with multiple atempo filters
                    if speed > 2.0:
                        # FFmpeg atempo filter is limited to 0.5 to 2.0 range
                        atempo_chain = 'atempo=2.0,'
                        remaining = speed / 2.0
                        while remaining > 2.0:
                            atempo_chain += 'atempo=2.0,'
                            remaining /= 2.0
                        atempo_chain += f'atempo={remaining}'

                        ffmpeg_cmd = [
                            'ffmpeg', '-y',
                            '-i', temp_path,
                            '-filter:a', atempo_chain,
                            '-vn', output_temp
                        ]
                    elif speed < 0.5:
                        # Similar approach for extreme slowdowns
                        atempo_chain = 'atempo=0.5,'
                        remaining = speed / 0.5
                        while remaining < 0.5:
                            atempo_chain += 'atempo=0.5,'
                            remaining /= 0.5
                        atempo_chain += f'atempo={remaining}'

                        ffmpeg_cmd = [
                            'ffmpeg', '-y',
                            '-i', temp_path,
                            '-filter:a', atempo_chain,
                            '-vn', output_temp
                        ]
                    else:
                        ffmpeg_cmd = [
                            'ffmpeg', '-y',
                            '-i', temp_path,
                            '-filter:a', f'atempo={speed}',
                            '-vn', output_temp
                        ]

                    subprocess.run(ffmpeg_cmd, capture_output=True)
                    final_audio = AudioSegment.from_file(output_temp)

                    # Clean up
                    os.remove(temp_path)
                    os.remove(output_temp)

            # Save final audio
            final_audio_path = os.path.join(output_dir, "tts_audio.mp3")
            final_audio.export(final_audio_path, format="mp3")

            return final_audio_path

        except Exception as e:
            raise Exception(f"Failed to generate TTS audio: {str(e)}")

    def _clean_text_for_tts(self, text):
        """
        Clean and prepare text for TTS generation

        Args:
            text (str): Raw text to clean

        Returns:
            str: Cleaned text suitable for TTS
        """
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

    def _split_text_into_chunks(self, text, max_chunk_size=500):
        """
        Split text into chunks suitable for Coqui TTS

        Args:
            text (str): Text to split
            max_chunk_size (int): Maximum characters per chunk

        Returns:
            list: List of text chunks
        """
        if len(text) <= max_chunk_size:
            return [text]

        chunks = []

        # Split by sentences
        sentences = re.split(r'([.!?]+)', text)

        current_chunk = ""

        for i in range(0, len(sentences), 2):
            sentence = sentences[i]
            punctuation = sentences[i + 1] if i + 1 < len(sentences) else ""

            full_sentence = sentence + punctuation

            # Check if adding this sentence would exceed the limit
            if len(current_chunk) + len(full_sentence) > max_chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = full_sentence
                else:
                    # Single sentence is too long, split by words
                    words = sentence.split()
                    word_chunk = ""

                    for word in words:
                        if len(word_chunk) + len(word) + 1 > max_chunk_size:
                            if word_chunk:
                                chunks.append(word_chunk.strip())
                                word_chunk = word
                            else:
                                # Single word is too long, truncate it
                                chunks.append(word[:max_chunk_size])
                        else:
                            word_chunk += " " + word if word_chunk else word

                    if word_chunk:
                        chunks.append(word_chunk.strip() + punctuation)
            else:
                current_chunk += full_sentence

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def get_available_voices(self):
        """
        Get dictionary of available TTS voices

        Returns:
            dict: Dictionary of available voice names and descriptions
        """
        return self.available_voices.copy()