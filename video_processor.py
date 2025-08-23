import os
import tempfile
from pytube import YouTube
import ffmpeg
import streamlit as st

class VideoProcessor:
    """Handles video downloading and processing operations"""
    
    def __init__(self):
        self.supported_formats = ['mp4', 'avi', 'mov', 'mkv', 'webm']
    
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
        Replace audio in video with new audio track using ffmpeg
        
        Args:
            video_path (str): Path to the original video
            new_audio_path (str): Path to the new audio file
            output_dir (str): Directory to save the output video
            
        Returns:
            str: Path to the output video with replaced audio
        """
        try:
            # Get video duration using ffmpeg
            video_info = ffmpeg.probe(video_path)
            video_duration = float(video_info['streams'][0]['duration'])
            
            # Get audio duration using ffmpeg
            audio_info = ffmpeg.probe(new_audio_path)
            audio_duration = float(audio_info['streams'][0]['duration'])
            
            # Output path
            output_path = os.path.join(output_dir, "output_video.mp4")
            
            # Handle duration mismatch and combine video with new audio
            video_input = ffmpeg.input(video_path)
            audio_input = ffmpeg.input(new_audio_path)
            
            if abs(audio_duration - video_duration) > 0.1:  # More than 0.1 second difference
                if audio_duration > video_duration:
                    # Trim audio to match video duration
                    audio_input = audio_input.filter('atrim', duration=video_duration)
                    st.warning(f"⚠️ Audio was longer than video. Trimmed to {video_duration:.1f} seconds.")
                else:
                    # Extend audio to match video duration by looping
                    audio_input = audio_input.filter('aloop', loop=-1, size=2e+09).filter('atrim', duration=video_duration)
                    st.warning(f"⚠️ Audio was shorter than video. Extended to {video_duration:.1f} seconds.")
            
            # Combine video and audio
            output = ffmpeg.output(
                video_input.video,
                audio_input.audio,
                output_path,
                vcodec='copy',  # Copy video stream without re-encoding
                acodec='aac',   # Re-encode audio as AAC
                strict='experimental'
            )
            
            # Run ffmpeg command
            ffmpeg.run(output, overwrite_output=True, quiet=True)
            
            return output_path
            
        except Exception as e:
            raise Exception(f"Failed to replace audio in video: {str(e)}")
    
    def get_video_info(self, video_path):
        """
        Get basic information about a video file using ffmpeg
        
        Args:
            video_path (str): Path to the video file
            
        Returns:
            dict: Video information including duration, fps, resolution
        """
        try:
            probe = ffmpeg.probe(video_path)
            
            video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
            audio_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
            
            info = {
                'duration': float(probe['format']['duration']) if 'duration' in probe['format'] else 0,
                'fps': eval(video_stream['r_frame_rate']) if video_stream and 'r_frame_rate' in video_stream else 0,
                'size': (int(video_stream['width']), int(video_stream['height'])) if video_stream else (0, 0),
                'has_audio': audio_stream is not None
            }
            
            return info
            
        except Exception as e:
            raise Exception(f"Failed to get video info: {str(e)}")
