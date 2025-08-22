import os
import tempfile
from pytube import YouTube
from moviepy.editor import VideoFileClip, AudioFileClip
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
        Replace audio in video with new audio track
        
        Args:
            video_path (str): Path to the original video
            new_audio_path (str): Path to the new audio file
            output_dir (str): Directory to save the output video
            
        Returns:
            str: Path to the output video with replaced audio
        """
        try:
            # Load video and audio clips
            video_clip = VideoFileClip(video_path)
            new_audio_clip = AudioFileClip(new_audio_path)
            
            # Get video duration
            video_duration = video_clip.duration
            audio_duration = new_audio_clip.duration
            
            # Handle duration mismatch
            if audio_duration > video_duration:
                # Trim audio to match video duration
                new_audio_clip = new_audio_clip.subclip(0, video_duration)
                st.warning(f"⚠️ Audio was longer than video. Trimmed to {video_duration:.1f} seconds.")
            elif audio_duration < video_duration:
                # Extend audio by repeating or padding with silence
                loops_needed = int(video_duration / audio_duration) + 1
                extended_audio = new_audio_clip
                
                for _ in range(loops_needed - 1):
                    extended_audio = extended_audio.concatenate_audioclip(new_audio_clip)
                
                # Trim to exact video duration
                extended_audio = extended_audio.subclip(0, video_duration)
                new_audio_clip = extended_audio
                st.warning(f"⚠️ Audio was shorter than video. Extended to {video_duration:.1f} seconds.")
            
            # Set the new audio to the video
            final_video = video_clip.set_audio(new_audio_clip)
            
            # Output path
            output_path = os.path.join(output_dir, "output_video.mp4")
            
            # Write the final video
            final_video.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile=os.path.join(output_dir, 'temp_audio.m4a'),
                remove_temp=True,
                verbose=False,
                logger=None  # Suppress moviepy logs
            )
            
            # Clean up clips
            video_clip.close()
            new_audio_clip.close()
            final_video.close()
            
            return output_path
            
        except Exception as e:
            raise Exception(f"Failed to replace audio in video: {str(e)}")
    
    def get_video_info(self, video_path):
        """
        Get basic information about a video file
        
        Args:
            video_path (str): Path to the video file
            
        Returns:
            dict: Video information including duration, fps, resolution
        """
        try:
            clip = VideoFileClip(video_path)
            
            info = {
                'duration': clip.duration,
                'fps': clip.fps,
                'size': clip.size,
                'has_audio': clip.audio is not None
            }
            
            clip.close()
            return info
            
        except Exception as e:
            raise Exception(f"Failed to get video info: {str(e)}")
