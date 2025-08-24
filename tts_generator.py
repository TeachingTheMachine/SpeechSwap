"""
Author: Vanessa Crosby
Date: August 23, 2025
File: tts_generator.py
Summary: Google Cloud Text-to-Speech generator with voice options and text processing
"""

import os
import tempfile
from google.cloud import texttospeech
from pydub import AudioSegment
import re

class TTSGenerator:
    """Handles text-to-speech generation using Google Cloud TTS"""

    def __init__(self):
        # Initialize Google Cloud TTS client
        # Google Cloud authentication can be done via:
        # 1. Service account key file (GOOGLE_APPLICATION_CREDENTIALS env var)
        # 2. Application Default Credentials (gcloud auth application-default login)
        # 3. Or automatic if running on Google Cloud
        self.client = texttospeech.TextToSpeechClient()

        # Available voices with language codes
        self.available_voices = {
            "en-US-Standard-A": "Female voice (US English)",
            "en-US-Standard-B": "Male voice (US English)", 
            "en-US-Standard-C": "Female voice (US English)",
            "en-US-Standard-D": "Male voice (US English)",
            "en-US-Neural2-A": "Neural Female voice (US English)",
            "en-US-Neural2-C": "Neural Female voice (US English)",
            "en-US-Neural2-D": "Neural Male voice (US English)",
            "en-US-Neural2-F": "Neural Female voice (US English)"
        }

    def generate_speech(self, text, output_dir, voice="en-US-Standard-A", speed=1.0):
        """
        Generate speech from text using Google Cloud TTS

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
                voice = "en-US-Standard-A"  # Default fallback

            speed = max(0.5, min(2.0, speed))  # Clamp speed to valid range for Google TTS

            # Clean and prepare text
            cleaned_text = self._clean_text_for_tts(text)

            if not cleaned_text.strip():
                raise Exception("No valid text found for TTS generation")

            # Split text into chunks if too long (Google TTS has character limits)
            text_chunks = self._split_text_into_chunks(cleaned_text, max_chunk_size=5000)

            # Generate audio for each chunk
            audio_segments = []

            for i, chunk in enumerate(text_chunks):
                chunk_audio_path = self._generate_chunk_audio(
                    chunk, output_dir, voice, speed, chunk_index=i
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

            # Save final audio
            final_audio_path = os.path.join(output_dir, "tts_audio.mp3")
            final_audio.export(final_audio_path, format="mp3")

            return final_audio_path

        except Exception as e:
            raise Exception(f"Failed to generate TTS audio: {str(e)}")

    def _generate_chunk_audio(self, text_chunk, output_dir, voice, speed, chunk_index=0):
        """
        Generate audio for a single text chunk using Google Cloud TTS

        Args:
            text_chunk (str): Text chunk to convert
            output_dir (str): Output directory
            voice (str): Voice to use
            speed (float): Speech speed
            chunk_index (int): Index of the chunk for file naming

        Returns:
            str: Path to the generated audio file
        """
        try:
            # Set the text input to be synthesized
            synthesis_input = texttospeech.SynthesisInput(text=text_chunk)

            # Build the voice request
            voice_params = texttospeech.VoiceSelectionParams(
                language_code="en-US",
                name=voice
            )

            # Select the type of audio file you want returned
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=speed
            )

            # Perform the text-to-speech request
            response = self.client.synthesize_speech(
                input=synthesis_input,
                voice=voice_params,
                audio_config=audio_config
            )

            # Save audio chunk
            chunk_path = os.path.join(output_dir, f"tts_chunk_{chunk_index}.mp3")

            with open(chunk_path, "wb") as f:
                f.write(response.audio_content)

            return chunk_path

        except Exception as e:
            raise Exception(f"Failed to generate audio chunk {chunk_index}: {str(e)}")

    def _clean_text_for_tts(self, text):
        """
        Clean and prepare text for TTS generation

        Args:
            text (str): Raw text to clean

        Returns:
            str: Cleaned text suitable for TTS
        """
        # Remove or replace problematic characters
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
        """
        Split text into chunks suitable for Google Cloud TTS API
        Google Cloud TTS has a limit of 5000 characters per request

        Args:
            text (str): Text to split
            max_chunk_size (int): Maximum characters per chunk

        Returns:
            list: List of text chunks
        """
        if len(text) <= max_chunk_size:
            return [text]

        chunks = []

        # Split by sentences first
        sentences = re.split(r'([.!?]+)', text)

        current_chunk = ""

        for i in range(0, len(sentences), 2):  # Step by 2 to include punctuation
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
                        current_chunk = word_chunk + punctuation
                    else:
                        current_chunk = punctuation
            else:
                current_chunk += full_sentence

        if current_chunk:
            chunks.append(current_chunk.strip())

        # Remove empty chunks
        chunks = [chunk for chunk in chunks if chunk.strip()]

        return chunks if chunks else [text[:max_chunk_size]]

    def get_available_voices(self):
        """
        Get dictionary of available TTS voices

        Returns:
            dict: Dictionary of available voice names and descriptions
        """
        return self.available_voices.copy()