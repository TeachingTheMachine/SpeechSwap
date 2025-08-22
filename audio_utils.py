import os
import tempfile
from moviepy.editor import VideoFileClip
from pydub import AudioSegment
from openai import OpenAI

class AudioUtils:
    """Handles audio extraction and processing operations"""
    
    def __init__(self):
        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not found in environment variables")
        
        self.openai_client = OpenAI(api_key=api_key)
    
    def extract_audio(self, video_path, output_dir):
        """
        Extract audio from video file
        
        Args:
            video_path (str): Path to the video file
            output_dir (str): Directory to save the extracted audio
            
        Returns:
            str: Path to the extracted audio file
        """
        try:
            # Load video clip
            video_clip = VideoFileClip(video_path)
            
            if not video_clip.audio:
                raise Exception("Video file has no audio track")
            
            # Extract audio
            audio_clip = video_clip.audio
            
            # Output path
            audio_path = os.path.join(output_dir, "extracted_audio.wav")
            
            # Write audio file
            audio_clip.write_audiofile(
                audio_path,
                verbose=False,
                logger=None  # Suppress moviepy logs
            )
            
            # Clean up clips
            audio_clip.close()
            video_clip.close()
            
            return audio_path
            
        except Exception as e:
            raise Exception(f"Failed to extract audio: {str(e)}")
    
    def transcribe_audio(self, audio_path):
        """
        Transcribe audio using OpenAI Whisper
        
        Args:
            audio_path (str): Path to the audio file
            
        Returns:
            str: Transcribed text
        """
        try:
            # Convert audio to format suitable for Whisper if needed
            processed_audio_path = self._prepare_audio_for_whisper(audio_path)
            
            # Transcribe using OpenAI Whisper
            with open(processed_audio_path, "rb") as audio_file:
                # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
                # do not change this unless explicitly requested by the user
                response = self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )
            
            # Clean up processed audio file if it's different from original
            if processed_audio_path != audio_path:
                os.remove(processed_audio_path)
            
            return response.strip()
            
        except Exception as e:
            raise Exception(f"Failed to transcribe audio: {str(e)}")
    
    def _prepare_audio_for_whisper(self, audio_path):
        """
        Prepare audio file for Whisper transcription
        Whisper works best with certain formats and sample rates
        
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
            
            # Set sample rate to 16kHz (good for speech recognition)
            audio = audio.set_frame_rate(16000)
            
            # Limit file size for API (max 25MB for Whisper)
            # If file is too long, we might need to chunk it
            max_duration_ms = 10 * 60 * 1000  # 10 minutes in milliseconds
            
            if len(audio) > max_duration_ms:
                audio = audio[:max_duration_ms]
                import streamlit as st
                st.warning("⚠️ Audio was truncated to 10 minutes for transcription.")
            
            # Export as MP3 for Whisper
            output_dir = os.path.dirname(audio_path)
            processed_path = os.path.join(output_dir, "whisper_audio.mp3")
            
            audio.export(processed_path, format="mp3", bitrate="64k")
            
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
