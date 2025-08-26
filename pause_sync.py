"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                pause_sync.py                                ║
║                                                                              ║
║  Author: Replit AI Assistant                                                 ║
║  Date Created: August 26, 2025                                              ║
║  Purpose: Pause-based audio synchronization system                          ║
║  Description: Analyzes pauses in both original and TTS audio for precise fit║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import tempfile
import subprocess
import json
import re


class PauseSync:
    """Pause-based audio synchronization using silence gap analysis"""
    
    def __init__(self):
        self.temp_files = []
        self.silence_threshold = -25  # dB
        self.min_silence_duration = 0.2  # seconds
    
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
    
    def extract_audio_for_analysis(self, video_path, output_path):
        """Extract audio from video in optimal format for analysis"""
        cmd = [
            'ffmpeg', '-y', '-i', video_path,
            '-ar', '22050',  # Standard sample rate
            '-ac', '1',      # Mono
            '-f', 'wav',     # WAV format for analysis
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Audio extraction failed: {result.stderr}")
        return output_path
    
    def analyze_pause_structure(self, audio_path, progress_callback=None):
        """
        Analyze pause/silence structure in audio file
        Returns: {
            'duration': total_duration,
            'segments': [(start, end, 'speech'/'silence'), ...],
            'speech_segments': [(start, end), ...],
            'silence_segments': [(start, end), ...]
        }
        """
        try:
            print(f"Analyzing pause structure in: {os.path.basename(audio_path)}")
            
            if progress_callback:
                progress_callback(10)
            
            # Use FFmpeg silencedetect filter with fine-tuned parameters
            cmd = [
                'ffmpeg', '-i', audio_path,
                '-af', f'silencedetect=noise={self.silence_threshold}dB:duration={self.min_silence_duration}',
                '-f', 'null', '-'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if progress_callback:
                progress_callback(50)
            
            # Parse FFmpeg output for silence detection
            silence_events = []
            for line in result.stderr.split('\n'):
                # Look for silence_start and silence_end
                if 'silence_start:' in line:
                    try:
                        time_str = line.split('silence_start: ')[1].strip()
                        silence_time = float(time_str)
                        silence_events.append(('start', silence_time))
                    except (IndexError, ValueError):
                        pass
                elif 'silence_end:' in line:
                    try:
                        # Extract just the time, ignore duration info
                        time_part = line.split('silence_end: ')[1].split(' ')[0].strip()
                        silence_time = float(time_part)
                        silence_events.append(('end', silence_time))
                    except (IndexError, ValueError):
                        pass
            
            if progress_callback:
                progress_callback(70)
            
            # Get total duration
            total_duration = self.get_audio_duration(audio_path)
            
            # Build segment structure
            segments = []
            speech_segments = []
            silence_segments = []
            
            current_time = 0.0
            silence_start = None
            
            for event_type, time in silence_events:
                if event_type == 'start':
                    # End of speech segment
                    if current_time < time:
                        segments.append((current_time, time, 'speech'))
                        speech_segments.append((current_time, time))
                    silence_start = time
                elif event_type == 'end' and silence_start is not None:
                    # End of silence segment
                    segments.append((silence_start, time, 'silence'))
                    silence_segments.append((silence_start, time))
                    current_time = time
                    silence_start = None
            
            # Handle final segment
            if current_time < total_duration:
                if silence_start is not None:
                    # Currently in silence
                    segments.append((silence_start, total_duration, 'silence'))
                    silence_segments.append((silence_start, total_duration))
                else:
                    # Currently in speech
                    segments.append((current_time, total_duration, 'speech'))
                    speech_segments.append((current_time, total_duration))
            
            if progress_callback:
                progress_callback(100)
            
            analysis = {
                'duration': total_duration,
                'segments': segments,
                'speech_segments': speech_segments,
                'silence_segments': silence_segments
            }
            
            print(f"Found {len(speech_segments)} speech segments and {len(silence_segments)} silence gaps")
            return analysis
            
        except Exception as e:
            raise Exception(f"Pause structure analysis failed: {str(e)}")
    
    def create_pause_mapping(self, original_analysis, tts_analysis):
        """
        Create mapping between original and TTS pause structures
        """
        orig_speech = original_analysis['speech_segments']
        tts_speech = tts_analysis['speech_segments']
        
        print(f"Mapping {len(orig_speech)} original segments to {len(tts_speech)} TTS segments")
        
        # Create segment mapping
        mappings = []
        
        # Simple approach: map segments by index, with proportional stretching
        max_segments = max(len(orig_speech), len(tts_speech))
        
        for i in range(max_segments):
            # Get original segment (or use last one if fewer original segments)
            if i < len(orig_speech):
                orig_start, orig_end = orig_speech[i]
            else:
                # Extend last segment proportionally
                if orig_speech:
                    last_start, last_end = orig_speech[-1]
                    segment_duration = last_end - last_start
                    orig_start = last_end
                    orig_end = orig_start + segment_duration
                else:
                    orig_start, orig_end = 0, original_analysis['duration']
            
            # Get TTS segment (or use last one if fewer TTS segments)
            if i < len(tts_speech):
                tts_start, tts_end = tts_speech[i]
            else:
                # Extend last segment proportionally
                if tts_speech:
                    last_start, last_end = tts_speech[-1]
                    segment_duration = last_end - last_start
                    tts_start = last_end
                    tts_end = tts_start + segment_duration
                else:
                    tts_start, tts_end = 0, tts_analysis['duration']
            
            # Calculate stretch factor for this segment
            orig_duration = orig_end - orig_start
            tts_duration = tts_end - tts_start
            
            if tts_duration > 0:
                stretch_factor = orig_duration / tts_duration
            else:
                stretch_factor = 1.0
            
            mappings.append({
                'tts_start': tts_start,
                'tts_end': tts_end,
                'target_start': orig_start,
                'target_end': orig_end,
                'stretch_factor': stretch_factor
            })
        
        return mappings
    
    def apply_pause_based_timing(self, tts_audio_path, mappings, output_path, progress_callback=None):
        """
        Apply pause-based timing adjustments using segment stretching
        """
        try:
            print("Applying pause-based timing adjustments")
            
            if progress_callback:
                progress_callback(10)
            
            # For now, use overall stretch factor approach
            # In future could implement per-segment stretching
            
            if not mappings:
                # Fallback: simple copy
                cmd = ['ffmpeg', '-y', '-i', tts_audio_path, '-acodec', 'copy', output_path]
            else:
                # Calculate weighted average stretch factor
                total_duration = sum(m['tts_end'] - m['tts_start'] for m in mappings)
                if total_duration > 0:
                    weighted_stretch = sum(
                        m['stretch_factor'] * (m['tts_end'] - m['tts_start']) 
                        for m in mappings
                    ) / total_duration
                else:
                    weighted_stretch = 1.0
                
                # Clamp stretch factor for quality
                stretch_factor = max(0.5, min(2.0, weighted_stretch))
                
                print(f"Applying stretch factor: {stretch_factor:.3f}")
                
                if progress_callback:
                    progress_callback(40)
                
                # Build FFmpeg command with atempo filters
                if abs(stretch_factor - 1.0) < 0.02:
                    # Very small change, just re-encode
                    cmd = [
                        'ffmpeg', '-y', '-i', tts_audio_path,
                        '-acodec', 'libmp3lame', '-q:a', '2',
                        output_path
                    ]
                else:
                    # Apply time stretching
                    filters = []
                    remaining_stretch = stretch_factor
                    
                    # Chain atempo filters for larger changes
                    while remaining_stretch > 2.0:
                        filters.append("atempo=2.0")
                        remaining_stretch /= 2.0
                    
                    while remaining_stretch < 0.5:
                        filters.append("atempo=0.5")
                        remaining_stretch *= 2.0
                    
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
                        cmd = [
                            'ffmpeg', '-y', '-i', tts_audio_path,
                            '-acodec', 'libmp3lame', '-q:a', '2',
                            output_path
                        ]
            
            if progress_callback:
                progress_callback(70)
            
            # Execute FFmpeg command
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"FFmpeg timing adjustment failed: {result.stderr}")
            
            if progress_callback:
                progress_callback(100)
            
            final_duration = self.get_audio_duration(output_path)
            print(f"Pause-based timing applied. Final duration: {final_duration:.2f}s")
            
            return output_path
            
        except Exception as e:
            raise Exception(f"Pause-based timing adjustment failed: {str(e)}")
    
    def synchronize_with_pause_analysis(self, video_path, tts_audio_path, output_dir, progress_callback=None):
        """
        Main method for pause-based audio synchronization
        """
        try:
            print("Starting pause-based audio synchronization")
            
            if progress_callback:
                progress_callback(5)
            
            # Extract original audio for analysis
            original_audio_path = os.path.join(output_dir, "original_for_pause_analysis.wav")
            self.temp_files.append(original_audio_path)
            
            self.extract_audio_for_analysis(video_path, original_audio_path)
            
            if progress_callback:
                progress_callback(15)
            
            # Analyze pause structure in original audio
            def orig_progress(p):
                if progress_callback:
                    progress_callback(15 + int(p * 0.25))
            
            original_analysis = self.analyze_pause_structure(original_audio_path, orig_progress)
            
            if progress_callback:
                progress_callback(40)
            
            # Analyze pause structure in TTS audio
            def tts_progress(p):
                if progress_callback:
                    progress_callback(40 + int(p * 0.25))
            
            tts_analysis = self.analyze_pause_structure(tts_audio_path, tts_progress)
            
            if progress_callback:
                progress_callback(65)
            
            # Create pause-based mapping
            mappings = self.create_pause_mapping(original_analysis, tts_analysis)
            
            if progress_callback:
                progress_callback(70)
            
            # Apply pause-based timing
            synchronized_audio_path = os.path.join(output_dir, "pause_synced_audio.mp3")
            
            def timing_progress(p):
                if progress_callback:
                    progress_callback(70 + int(p * 0.3))
            
            result_path = self.apply_pause_based_timing(
                tts_audio_path, mappings, synchronized_audio_path, timing_progress
            )
            
            if progress_callback:
                progress_callback(100)
            
            print("Pause-based synchronization complete")
            return result_path
            
        except Exception as e:
            raise Exception(f"Pause-based synchronization failed: {str(e)}")
        finally:
            # Clean up temporary files
            self.cleanup_temp_files()