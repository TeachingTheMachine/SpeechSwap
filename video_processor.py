"""
Author: Vanessa Crosby
Date: August 23, 2025
File: video_processor.py
Summary: Handles YouTube transcript extraction and video processing operations
"""

import os
import tempfile
import subprocess
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp
from pydub import AudioSegment
import streamlit as st
import re

class VideoProcessor:
    """Handles video downloading and processing operations"""

    def __init__(self):
        self.supported_formats = ['mp4', 'avi', 'mov', 'mkv', 'webm']

    def extract_video_id(self, youtube_url):
        """Extract video ID from YouTube URL"""
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)',
            r'youtube\.com\/embed\/([^&\n?#]+)',
            r'youtube\.com\/v\/([^&\n?#]+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, youtube_url)
            if match:
                return match.group(1)

        raise ValueError("Could not extract video ID from URL")

    def get_youtube_transcript(self, youtube_url):
        """
        Get transcript from YouTube video using YouTube Transcript API
        This is much more reliable than downloading the video

        Args:
            youtube_url (str): YouTube video URL

        Returns:
            str: Transcript text
        """
        try:
            # Extract video ID
            video_id = self.extract_video_id(youtube_url)

            # Initialize the YouTube Transcript API
            ytt_api = YouTubeTranscriptApi()

            # Get list of available transcripts
            transcript_list = ytt_api.list(video_id)

            # Try to find English transcript (prefer manual over auto-generated)
            try:
                english_transcript = transcript_list.find_transcript(['en', 'en-US', 'en-GB'])
            except:
                # If no English transcript, try any available language
                available_transcripts = list(transcript_list)
                if not available_transcripts:
                    raise Exception("No transcripts available for this video")
                english_transcript = available_transcripts[0]

            # Fetch the transcript data
            fetched_data = english_transcript.fetch()

            # Extract text from FetchedTranscriptSnippet objects
            full_transcript = ' '.join([snippet.text for snippet in fetched_data.snippets])

            # Clean up the transcript
            full_transcript = self._clean_transcript(full_transcript)

            return full_transcript

        except Exception as e:
            # If direct transcript fails, try alternative methods
            return self._fallback_transcript_extraction(youtube_url)

    def _clean_transcript(self, transcript):
        """Clean up transcript text"""
        # Remove excessive whitespace
        transcript = re.sub(r'\s+', ' ', transcript)

        # Remove common transcript artifacts
        transcript = re.sub(r'\[.*?\]', '', transcript)  # Remove [Music], [Applause], etc.
        transcript = re.sub(r'\(.*?\)', '', transcript)  # Remove parenthetical notes

        # Fix common transcription issues
        transcript = transcript.replace(' uh ', ' ')
        transcript = transcript.replace(' um ', ' ')
        transcript = transcript.replace(' er ', ' ')

        return transcript.strip()

    def _fallback_transcript_extraction(self, youtube_url):
        """
        Fallback method using yt-dlp to extract subtitles
        """
        try:
            video_id = self.extract_video_id(youtube_url)

            ydl_opts = {
                'writesubtitles': True,
                'writeautomaticsub': True,
                'skip_download': True,
                'quiet': True,
                'no_warnings': True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(youtube_url, download=False)

                # Look for subtitles
                subtitles = info_dict.get('subtitles', {})
                auto_captions = info_dict.get('automatic_captions', {})

                # Try English subtitles first
                for lang in ['en', 'en-US', 'en-GB']:
                    if lang in subtitles:
                        # Download subtitle file
                        return self._extract_text_from_subtitles(subtitles[lang])
                    elif lang in auto_captions:
                        return self._extract_text_from_subtitles(auto_captions[lang])

                # If no English subtitles, try any available language
                all_subs = {**subtitles, **auto_captions}
                if all_subs:
                    first_lang = list(all_subs.keys())[0]
                    return self._extract_text_from_subtitles(all_subs[first_lang])

                raise Exception("No subtitles found for this video")

        except Exception as e:
            raise Exception(f"Could not extract transcript: {str(e)}")

    def _extract_text_from_subtitles(self, subtitle_formats):
        """Extract text from subtitle format info"""
        # This is a simplified version - you might need to expand this
        # based on the actual subtitle format structure
        try:
            # Look for VTT format (most common)
            vtt_format = next((fmt for fmt in subtitle_formats if fmt.get('ext') == 'vtt'), None)
            if vtt_format:
                # In a real implementation, you'd download and parse the VTT file
                # For now, return a placeholder
                return "Transcript extraction from subtitles not fully implemented"

            return "Could not extract text from available subtitle formats"

        except Exception:
            return "Error processing subtitle formats"

    def download_youtube_video(self, url, output_dir):
        """
        DEPRECATED: This method now only gets transcript, doesn't download video
        Use get_youtube_transcript() directly instead

        Args:
            url (str): YouTube video URL
            output_dir (str): Directory (not used anymore)

        Returns:
            str: Returns "TRANSCRIPT_ONLY" to indicate this is transcript-only mode
        """
        # For backward compatibility, just get transcript
        transcript = self.get_youtube_transcript(url)

        # Save transcript to a temp file for compatibility
        transcript_path = os.path.join(output_dir, "transcript.txt")
        with open(transcript_path, 'w', encoding='utf-8') as f:
            f.write(transcript)

        return "TRANSCRIPT_ONLY"

    def _get_duration(self, file_path):
        """Get duration of a media file using ffprobe"""
        if file_path == "TRANSCRIPT_ONLY":
            return 0  # Return 0 for transcript-only mode

        cmd = [
            'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
            '-of', 'csv=p=0', file_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return float(result.stdout.strip())
        return 0

    def replace_audio(self, video_path, new_audio_path, output_dir):
        """
        Replace audio in video with new audio track using ffmpeg subprocess

        Args:
            video_path (str): Path to the original video (or "TRANSCRIPT_ONLY")
            new_audio_path (str): Path to the new audio file
            output_dir (str): Directory to save the output video

        Returns:
            str: Path to the output video with replaced audio or just the audio file
        """
        try:
            if video_path == "TRANSCRIPT_ONLY":
                # In transcript-only mode, just return the generated audio
                output_path = os.path.join(output_dir, "output_audio.mp3")
                # Copy the audio file
                import shutil
                shutil.copy2(new_audio_path, output_path)
                return output_path

            # Original video processing logic
            video_duration = self._get_duration(video_path)
            audio_duration = self._get_duration(new_audio_path)

            # Output path
            output_path = os.path.join(output_dir, "output_video.mp4")

            # Build ffmpeg command to combine video with new audio
            cmd = [
                'ffmpeg', '-y',  # Overwrite output file
                '-i', video_path,  # Input video
                '-i', new_audio_path,  # Input audio
                '-c:v', 'copy',  # Copy video stream
                '-c:a', 'aac',   # Encode audio as AAC
                '-map', '0:v:0',  # Map video from first input
                '-map', '1:a:0',  # Map audio from second input
            ]

            # Handle duration mismatch
            if abs(audio_duration - video_duration) > 0.1:  # More than 0.1 second difference
                if audio_duration > video_duration:
                    # Trim audio to match video duration
                    cmd.extend(['-t', str(video_duration)])
                    st.warning(f"⚠️ Audio was longer than video. Trimmed to {video_duration:.1f} seconds.")
                else:
                    # Loop audio to match video duration
                    cmd.extend(['-stream_loop', '-1', '-t', str(video_duration)])
                    st.warning(f"⚠️ Audio was shorter than video. Extended to {video_duration:.1f} seconds.")

            cmd.append(output_path)

            # Run ffmpeg command
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                raise Exception(f"FFmpeg failed: {result.stderr}")

            return output_path

        except Exception as e:
            raise Exception(f"Failed to replace audio in video: {str(e)}")

    def get_video_info(self, video_path):
        """
        Get basic information about a video file using ffprobe subprocess

        Args:
            video_path (str): Path to the video file

        Returns:
            dict: Video information including duration, fps, resolution
        """
        try:
            if video_path == "TRANSCRIPT_ONLY":
                return {
                    'duration': 0,
                    'fps': 0,
                    'size': (0, 0),
                    'has_audio': False,
                    'transcript_only': True
                }

            # Use ffprobe to get video information
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', video_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                raise Exception(f"FFprobe failed: {result.stderr}")

            import json
            probe_data = json.loads(result.stdout)

            video_stream = next((stream for stream in probe_data['streams'] if stream['codec_type'] == 'video'), None)
            audio_stream = next((stream for stream in probe_data['streams'] if stream['codec_type'] == 'audio'), None)

            info = {
                'duration': float(probe_data['format']['duration']) if 'duration' in probe_data['format'] else 0,
                'fps': eval(video_stream['r_frame_rate']) if video_stream and 'r_frame_rate' in video_stream else 0,
                'size': (int(video_stream['width']), int(video_stream['height'])) if video_stream else (0, 0),
                'has_audio': audio_stream is not None,
                'transcript_only': False
            }

            return info

        except Exception as e:
            raise Exception(f"Failed to get video info: {str(e)}")