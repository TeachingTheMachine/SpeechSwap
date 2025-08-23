import os
import tempfile
import subprocess
from pytube import YouTube
from pydub import AudioSegment
import streamlit as st

class VideoProcessor:
    """Handles video downloading and processing operations"""
    
    def __init__(self):
        self.supported_formats = ['mp4', 'avi', 'mov', 'mkv', 'webm']
    
    def _get_duration(self, file_path):
        """Get duration of a media file using ffprobe"""
        cmd = [
            'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
            '-of', 'csv=p=0', file_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return float(result.stdout.strip())
        return 0
    
    def download_youtube_video(self, url, output_dir):
        """
        Download YouTube video
        
        Args:
            url (str): YouTube video URL
            output_dir (str): Directory to save the video
            
        Returns:
            str: Path to the downloaded video file
        """
        try:
            # Create YouTube object
            yt = YouTube(url)
            
            # Get the highest quality progressive stream (video + audio)
            stream = yt.streams.filter(
                progressive=True, 
                file_extension='mp4'
            ).order_by('resolution').desc().first()
            
            if not stream:
                # If no progressive stream, get highest quality video stream
                stream = yt.streams.filter(
                    adaptive=True,
                    file_extension='mp4',
                    only_video=False
                ).order_by('resolution').desc().first()
            
            if not stream:
                raise Exception("No suitable video stream found")
            
            # Download the video
            output_path = stream.download(
                output_path=output_dir,
                filename="youtube_video.mp4"
            )
            
            return output_path
            
        except Exception as e:
            raise Exception(f"Failed to download YouTube video: {str(e)}")
    
    def replace_audio(self, video_path, new_audio_path, output_dir):
        """
        Replace audio in video with new audio track using ffmpeg subprocess
        
        Args:
            video_path (str): Path to the original video
            new_audio_path (str): Path to the new audio file
            output_dir (str): Directory to save the output video
            
        Returns:
            str: Path to the output video with replaced audio
        """
        try:
            # Get video duration using ffprobe subprocess
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
                'has_audio': audio_stream is not None
            }
            
            return info
            
        except Exception as e:
            raise Exception(f"Failed to get video info: {str(e)}")
