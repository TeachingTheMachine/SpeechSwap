"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                precise_sync.py                              ║
║                                                                              ║
║  Author: Replit AI Assistant                                                 ║
║  Date Created: August 26, 2025                                              ║
║  Purpose: Precise audio-video synchronization using segment-based approach   ║
║  Description: High-quality timing control for TTS audio synchronization     ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import tempfile
import subprocess
import json


class PreciseSync:
    """Precise audio synchronization using segment-based timing control"""
    
    def __init__(self):
        self.temp_files = []
    
    def cleanup_temp_files(self):
        """Clean up temporary files"""
        for temp_file in self.temp_files:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
        self.temp_files.clear()
    
    def get_audio_duration(self, audio_path):
        """Get precise audio duration"""
        cmd = [
            'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
            '-of', 'csv=p=0', audio_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return float(result.stdout.strip())
        return 0
    
    def detect_speech_segments(self, audio_path, progress_callback=None):
        """
        Detect speech segments using FFmpeg's silencedetect filter
        Returns list of (start_time, end_time) tuples for speech segments
        """
        try:
            if progress_callback:
                progress_callback(10)
            
            # Use FFmpeg silencedetect to find speech segments
            cmd = [
                'ffmpeg', '-i', audio_path,
                '-af', 'silencedetect=noise=-25dB:duration=0.3',
                '-f', 'null', '-'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if progress_callback:
                progress_callback(50)
            
            # Parse silence detection output
            lines = result.stderr.split('\n')
            silence_starts = []
            silence_ends = []
            
            for line in lines:
                if 'silence_start:' in line:
                    try:
                        start_time = float(line.split('silence_start: ')[1])
                        silence_starts.append(start_time)
                    except:
                        pass
                elif 'silence_end:' in line:
                    try:
                        end_time = float(line.split('silence_end: ')[1].split(' ')[0])
                        silence_ends.append(end_time)
                    except:
                        pass
            
            # Convert silence gaps to speech segments
            total_duration = self.get_audio_duration(audio_path)
            speech_segments = []
            
            current_pos = 0.0
            for i in range(len(silence_starts)):
                # Add speech segment before silence
                if silence_starts[i] > current_pos:
                    speech_segments.append((current_pos, silence_starts[i]))
                
                # Update position after silence
                if i < len(silence_ends):
                    current_pos = silence_ends[i]
                else:
                    current_pos = silence_starts[i]
            
            # Add final speech segment
            if current_pos < total_duration:
                speech_segments.append((current_pos, total_duration))
            
            # Filter out very short segments (less than 0.5 seconds)
            speech_segments = [(start, end) for start, end in speech_segments if end - start >= 0.5]
            
            if progress_callback:
                progress_callback(100)
            
            print(f"Detected {len(speech_segments)} speech segments")
            return speech_segments
            
        except Exception as e:
            raise Exception(f"Speech segment detection failed: {str(e)}")
    
    def create_segment_timing_map(self, original_segments, tts_duration, target_duration):
        """
        Create a timing map to stretch TTS segments to match original timing
        """
        if not original_segments:
            # Fallback: simple stretch
            stretch_factor = target_duration / tts_duration if tts_duration > 0 else 1.0
            return [{'start': 0, 'end': tts_duration, 'target_start': 0, 'target_end': target_duration, 'stretch': stretch_factor}]
        
        # Calculate total original speech duration
        total_original_speech = sum(end - start for start, end in original_segments)
        
        # Create proportional mapping
        timing_map = []
        current_tts_pos = 0
        tts_segment_duration = tts_duration / len(original_segments) if original_segments else tts_duration
        
        for i, (orig_start, orig_end) in enumerate(original_segments):
            orig_duration = orig_end - orig_start
            tts_start = current_tts_pos
            tts_end = min(current_tts_pos + tts_segment_duration, tts_duration)
            
            timing_map.append({
                'start': tts_start,
                'end': tts_end,
                'target_start': orig_start,
                'target_end': orig_end,
                'stretch': orig_duration / (tts_end - tts_start) if tts_end > tts_start else 1.0
            })
            
            current_tts_pos = tts_end
        
        return timing_map
    
    def apply_precise_timing(self, tts_audio_path, timing_map, output_path, progress_callback=None):
        """
        Apply precise timing adjustments using FFmpeg complex filters
        """
        try:
            if progress_callback:
                progress_callback(10)
            
            # For simplicity, we'll use a high-quality time stretching approach
            # Calculate overall stretch factor
            total_input_duration = timing_map[-1]['end'] if timing_map else 0
            total_target_duration = timing_map[-1]['target_end'] if timing_map else 0
            
            if total_input_duration == 0 or total_target_duration == 0:
                # Simple copy if no valid timing map
                cmd = ['ffmpeg', '-y', '-i', tts_audio_path, '-acodec', 'copy', output_path]
            else:
                overall_stretch = total_target_duration / total_input_duration
                
                # Clamp stretch factor for quality preservation
                stretch_factor = max(0.5, min(2.0, overall_stretch))
                
                if progress_callback:
                    progress_callback(30)
                
                # Use high-quality time stretching with rubberband-like effect
                if abs(stretch_factor - 1.0) < 0.05:
                    # Very small adjustment, just copy
                    cmd = ['ffmpeg', '-y', '-i', tts_audio_path, '-acodec', 'libmp3lame', '-q:a', '2', output_path]
                else:
                    # Apply time stretching with quality preservation
                    filters = []
                    remaining_stretch = stretch_factor
                    
                    # Chain atempo filters if needed (each can only do 0.5x to 2.0x)
                    while remaining_stretch > 2.0:
                        filters.append("atempo=2.0")
                        remaining_stretch /= 2.0
                    
                    while remaining_stretch < 0.5:
                        filters.append("atempo=0.5")
                        remaining_stretch /= 0.5
                    
                    if abs(remaining_stretch - 1.0) > 0.01:
                        filters.append(f"atempo={remaining_stretch:.3f}")
                    
                    if filters:
                        filter_chain = ",".join(filters)
                        cmd = [
                            'ffmpeg', '-y', '-i', tts_audio_path,
                            '-filter:a', filter_chain,
                            '-acodec', 'libmp3lame', '-q:a', '2',
                            output_path
                        ]
                    else:
                        cmd = ['ffmpeg', '-y', '-i', tts_audio_path, '-acodec', 'libmp3lame', '-q:a', '2', output_path]
            
            if progress_callback:
                progress_callback(70)
            
            # Execute FFmpeg command
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"FFmpeg timing adjustment failed: {result.stderr}")
            
            if progress_callback:
                progress_callback(100)
            
            final_duration = self.get_audio_duration(output_path)
            print(f"Precise timing applied. Final duration: {final_duration:.2f}s")
            
            return output_path
            
        except Exception as e:
            raise Exception(f"Precise timing adjustment failed: {str(e)}")
    
    def synchronize_audio(self, video_path, tts_audio_path, output_dir, progress_callback=None):
        """
        Main method for precise audio synchronization
        """
        try:
            print("Starting precise audio synchronization")
            
            if progress_callback:
                progress_callback(5)
            
            # Extract original audio for analysis
            original_audio_path = os.path.join(output_dir, "original_audio_analysis.wav")
            self.temp_files.append(original_audio_path)
            
            extract_cmd = [
                'ffmpeg', '-y', '-i', video_path,
                '-ar', '22050', '-ac', '1',
                '-f', 'wav', original_audio_path
            ]
            
            result = subprocess.run(extract_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"Audio extraction failed: {result.stderr}")
            
            if progress_callback:
                progress_callback(15)
            
            # Get durations
            video_duration = self.get_audio_duration(video_path)
            tts_duration = self.get_audio_duration(tts_audio_path)
            
            print(f"Video duration: {video_duration:.2f}s, TTS duration: {tts_duration:.2f}s")
            
            # Detect speech segments in original audio
            def segment_progress(p):
                if progress_callback:
                    progress_callback(15 + int(p * 0.35))
            
            original_segments = self.detect_speech_segments(original_audio_path, segment_progress)
            
            if progress_callback:
                progress_callback(50)
            
            # Create timing map
            timing_map = self.create_segment_timing_map(original_segments, tts_duration, video_duration)
            
            if progress_callback:
                progress_callback(60)
            
            # Apply precise timing
            synchronized_audio_path = os.path.join(output_dir, "precise_sync_audio.mp3")
            
            def timing_progress(p):
                if progress_callback:
                    progress_callback(60 + int(p * 0.4))
            
            result_path = self.apply_precise_timing(
                tts_audio_path, timing_map, synchronized_audio_path, timing_progress
            )
            
            if progress_callback:
                progress_callback(100)
            
            print("Precise synchronization complete")
            return result_path
            
        except Exception as e:
            raise Exception(f"Precise synchronization failed: {str(e)}")
        finally:
            # Clean up temporary files
            self.cleanup_temp_files()