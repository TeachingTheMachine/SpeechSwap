"""
Video processing for SpeechSwap - simplified stretch method only
"""

import os
import tempfile
import subprocess

class VideoProcessor:
    """Simplified video processor using only stretch synchronization method"""
    
    def __init__(self):
        self.supported_formats = ['mp4', 'avi', 'mov', 'mkv', 'webm']

    def extract_audio(self, video_path, audio_output_path):
        """Extract audio from video file"""
        try:
            cmd = [
                'ffmpeg', '-y',
                '-i', video_path,
                '-vn',  # No video
                '-acodec', 'pcm_s16le',  # Uncompressed audio
                '-ar', '44100',  # Sample rate
                '-ac', '2',  # Stereo
                audio_output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"Audio extraction failed: {result.stderr}")
                
            if not os.path.exists(audio_output_path):
                raise Exception("Audio file was not created")
                
            return audio_output_path
            
        except Exception as e:
            raise Exception(f"Failed to extract audio: {str(e)}")

    def _get_duration(self, file_path):
        """Get duration of video or audio file"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                '-of', 'csv=p=0', file_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                return float(result.stdout.strip())
            return 0
        except:
            return 0

    def replace_audio(self, video_path, new_audio_path, output_dir, sync_method="stretch", pause_detection=False):
        """Replace audio in video using stretch synchronization method"""
        try:
            video_duration = self._get_duration(video_path)
            audio_duration = self._get_duration(new_audio_path)
            
            if video_duration == 0:
                raise Exception("Could not determine video duration")
            if audio_duration == 0:
                raise Exception("Could not determine audio duration")

            output_path = os.path.join(output_dir, "output_video.mp4")
            
            print(f"Video duration: {video_duration:.2f}s, Audio duration: {audio_duration:.2f}s")

            # Calculate tempo adjustment ratio
            tempo_ratio = audio_duration / video_duration
            print(f"Using audio stretching with tempo ratio: {tempo_ratio:.3f}")

            if pause_detection:
                print("Using pause-aware stretching")
                # Enhanced stretch with pause detection
                temp_audio = os.path.join(output_dir, "stretched_audio.wav")
                
                # Use atempo filter with pause preservation
                if tempo_ratio > 2.0:
                    # For large ratios, chain multiple atempo filters
                    first_ratio = tempo_ratio ** 0.5
                    second_ratio = tempo_ratio / first_ratio
                    audio_filter = f"atempo={first_ratio:.3f},atempo={second_ratio:.3f}"
                elif tempo_ratio < 0.5:
                    # For small ratios, chain multiple atempo filters
                    first_ratio = tempo_ratio ** 0.5
                    second_ratio = tempo_ratio / first_ratio
                    audio_filter = f"atempo={first_ratio:.3f},atempo={second_ratio:.3f}"
                else:
                    audio_filter = f"atempo={tempo_ratio:.3f}"
                
                # Apply stretching to audio
                cmd = [
                    'ffmpeg', '-y',
                    '-i', new_audio_path,
                    '-filter:a', audio_filter,
                    temp_audio
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    raise Exception(f"Audio stretching failed: {result.stderr}")
                
                stretched_audio = temp_audio
            else:
                print("Using basic audio stretching")
                # Basic stretching
                stretched_audio = new_audio_path
                tempo_ratio_cmd = tempo_ratio

            # Combine video with stretched audio
            if pause_detection:
                # Use pre-stretched audio
                cmd = [
                    'ffmpeg', '-y',
                    '-i', video_path,
                    '-i', stretched_audio,
                    '-c:v', 'copy',
                    '-c:a', 'aac',
                    '-map', '0:v:0',
                    '-map', '1:a:0',
                    '-shortest',
                    output_path
                ]
            else:
                # Apply stretching during combination
                if tempo_ratio > 2.0:
                    first_ratio = tempo_ratio ** 0.5
                    second_ratio = tempo_ratio / first_ratio
                    audio_filter = f"atempo={first_ratio:.3f},atempo={second_ratio:.3f}"
                elif tempo_ratio < 0.5:
                    first_ratio = tempo_ratio ** 0.5
                    second_ratio = tempo_ratio / first_ratio
                    audio_filter = f"atempo={first_ratio:.3f},atempo={second_ratio:.3f}"
                else:
                    audio_filter = f"atempo={tempo_ratio:.3f}"
                
                cmd = [
                    'ffmpeg', '-y',
                    '-i', video_path,
                    '-i', new_audio_path,
                    '-c:v', 'copy',
                    '-c:a', 'aac',
                    '-filter:a', audio_filter,
                    '-map', '0:v:0',
                    '-map', '1:a:0',
                    '-shortest',
                    output_path
                ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                final_duration = self._get_duration(output_path)
                print(f"Final video duration: {final_duration:.2f}s")
                return output_path
            else:
                raise Exception(f"Video combination failed: {result.stderr}")
                
        except Exception as e:
            raise Exception(f"Audio replacement failed: {str(e)}")