"""
Author: Vanessa Crosby
Date: August 23, 2025
File: audio_utils.py
Summary: Audio processing utilities for extraction transcription and Google Cloud Speech
"""

import os
import tempfile
import subprocess
from pydub import AudioSegment
from google.cloud import speech

class AudioUtils:
    """Handles audio extraction and processing operations"""

    def __init__(self):
        # Initialize Google Cloud Speech client
        # Google Cloud authentication can be done via:
        # 1. Service account key file (GOOGLE_APPLICATION_CREDENTIALS env var)
        # 2. Application Default Credentials (gcloud auth application-default login)
        # 3. Or automatic if running on Google Cloud
        self.speech_client = speech.SpeechClient()

    def extract_audio(self, video_path, output_dir):
        """
        Extract audio from video file using ffmpeg subprocess

        Args:
            video_path (str): Path to the video file or "TRANSCRIPT_ONLY"
            output_dir (str): Directory to save the extracted audio

        Returns:
            str: Path to the extracted audio file or "TRANSCRIPT_ONLY"
        """
        # Handle transcript-only mode
        if video_path == "TRANSCRIPT_ONLY":
            return "TRANSCRIPT_ONLY"

        try:
            # Check if video has audio stream using ffprobe
            probe_cmd = [
                'ffprobe', '-v', 'quiet', '-select_streams', 'a:0',
                '-show_entries', 'stream=codec_type', '-of', 'csv=p=0', video_path
            ]

            probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)

            if probe_result.returncode != 0 or 'audio' not in probe_result.stdout:
                raise Exception("Video file has no audio track")

            # Output path
            audio_path = os.path.join(output_dir, "extracted_audio.wav")

            # Extract audio using ffmpeg subprocess
            extract_cmd = [
                'ffmpeg', '-y',  # Overwrite output
                '-i', video_path,  # Input video
                '-vn',  # No video
                '-acodec', 'pcm_s16le',  # 16-bit PCM
                '-ac', '1',  # Mono
                '-ar', '16000',  # 16kHz sample rate for speech recognition
                audio_path
            ]

            result = subprocess.run(extract_cmd, capture_output=True, text=True)

            if result.returncode != 0:
                raise Exception(f"FFmpeg failed: {result.stderr}")

            return audio_path

        except Exception as e:
            raise Exception(f"Failed to extract audio: {str(e)}")

    def transcribe_audio(self, audio_path, transcript_text=None):
        """
        Transcribe audio using Google Cloud Speech-to-Text OR use provided transcript

        Args:
            audio_path (str): Path to the audio file or "TRANSCRIPT_ONLY"
            transcript_text (str, optional): Pre-existing transcript text

        Returns:
            str: Transcribed text
        """
        # If we have a pre-existing transcript (from YouTube), use it
        if audio_path == "TRANSCRIPT_ONLY" and transcript_text:
            return transcript_text

        # If we have transcript text but also audio, we can choose which to use
        if transcript_text and audio_path != "TRANSCRIPT_ONLY":
            import streamlit as st
            st.info("✨ Using YouTube's transcript instead of audio transcription for better accuracy!")
            return transcript_text

        # If no transcript provided and audio_path is "TRANSCRIPT_ONLY", that's an error
        if audio_path == "TRANSCRIPT_ONLY" and not transcript_text:
            raise Exception("No transcript available and no audio to transcribe")

        # Original audio transcription logic for uploaded video files
        try:
            # Convert audio to format suitable for Google Speech-to-Text if needed
            processed_audio_path = self._prepare_audio_for_speech_api(audio_path)

            # Read the audio file
            with open(processed_audio_path, "rb") as audio_file:
                content = audio_file.read()

            # Configure recognition
            audio = speech.RecognitionAudio(content=content)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code="en-US",
                # Enable automatic punctuation and word confidence
                enable_automatic_punctuation=True,
                # Use enhanced model for better accuracy
                use_enhanced=True,
                # Alternative: use latest long-running recognition for longer audio
                model="latest_long"
            )

            # Perform the transcription
            response = self.speech_client.recognize(config=config, audio=audio)

            # Combine all transcription results
            transcript_parts = []
            for result in response.results:
                transcript_parts.append(result.alternatives[0].transcript)

            transcript = " ".join(transcript_parts)

            # Clean up processed audio file if it's different from original
            if processed_audio_path != audio_path:
                os.remove(processed_audio_path)

            return transcript.strip()

        except Exception as e:
            raise Exception(f"Failed to transcribe audio: {str(e)}")

    def get_transcript_from_file(self, output_dir):
        """
        Read transcript from saved transcript file (for transcript-only mode)

        Args:
            output_dir (str): Directory containing transcript.txt

        Returns:
            str: Transcript text or None if not found
        """
        transcript_path = os.path.join(output_dir, "transcript.txt")
        if os.path.exists(transcript_path):
            with open(transcript_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        return None

    def _prepare_audio_for_speech_api(self, audio_path):
        """
        Prepare audio file for Google Cloud Speech-to-Text transcription
        Google Speech-to-Text works best with specific formats and sample rates

        Args:
            audio_path (str): Path to the original audio file

        Returns:
            str: Path to the processed audio file
        """
        try:
            # Load audio using pydub
            audio = AudioSegment.from_file(audio_path)

            # Convert to mono if stereo
            if audio.channels > 1:
                audio = audio.set_channels(1)

            # Set sample rate to 16kHz (required for Google Speech-to-Text)
            audio = audio.set_frame_rate(16000)

            # Limit file size for API (max 10MB for synchronous recognition)
            # If file is too long, we might need to use asynchronous recognition
            max_duration_ms = 5 * 60 * 1000  # 5 minutes in milliseconds for sync API

            if len(audio) > max_duration_ms:
                audio = audio[:max_duration_ms]
                import streamlit as st
                st.warning("⚠️ Audio was truncated to 5 minutes for transcription.")

            # Export as WAV for Google Speech-to-Text (LINEAR16 encoding)
            output_dir = os.path.dirname(audio_path)
            processed_path = os.path.join(output_dir, "speech_audio.wav")

            audio.export(processed_path, format="wav")

            return processed_path

        except Exception as e:
            # If processing fails, return original file
            return audio_path

    def get_audio_duration(self, audio_path):
        """
        Get duration of audio file in seconds

        Args:
            audio_path (str): Path to the audio file

        Returns:
            float: Duration in seconds
        """
        try:
            if audio_path == "TRANSCRIPT_ONLY":
                return 0

            audio = AudioSegment.from_file(audio_path)
            return len(audio) / 1000.0  # Convert milliseconds to seconds

        except Exception as e:
            raise Exception(f"Failed to get audio duration: {str(e)}")

    def normalize_audio_volume(self, audio_path, target_dBFS=-20.0):
        """
        Normalize audio volume to target level

        Args:
            audio_path (str): Path to the audio file
            target_dBFS (float): Target volume level in dBFS

        Returns:
            str: Path to the normalized audio file
        """
        try:
            if audio_path == "TRANSCRIPT_ONLY":
                return "TRANSCRIPT_ONLY"

            audio = AudioSegment.from_file(audio_path)

            # Calculate the change needed
            change_in_dBFS = target_dBFS - audio.dBFS

            # Apply volume change
            normalized_audio = audio.apply_gain(change_in_dBFS)

            # Save normalized audio
            output_dir = os.path.dirname(audio_path)
            normalized_path = os.path.join(output_dir, "normalized_audio.wav")

            normalized_audio.export(normalized_path, format="wav")

            return normalized_path

        except Exception as e:
            raise Exception(f"Failed to normalize audio: {str(e)}")