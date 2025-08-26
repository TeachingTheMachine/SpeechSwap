"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                              audio_synchronizer.py                         ║
║                                                                              ║
║  Author: Replit AI Assistant                                                 ║
║  Date Created: August 26, 2025                                              ║
║  Purpose: Advanced audio synchronization for YouTube Voice Replacement      ║
║  Description: Intelligent speech pattern analysis for better lip sync       ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import tempfile
import subprocess
import hashlib
import json
import pickle
from pathlib import Path
import streamlit as st

# Try to import advanced audio analysis libraries
try:
    import numpy as np
    import librosa
    ADVANCED_ANALYSIS_AVAILABLE = True
    print("Advanced audio analysis available (librosa + numpy)")
except ImportError:
    ADVANCED_ANALYSIS_AVAILABLE = False
    print("Advanced audio analysis not available - using basic methods")
    # Create basic numpy-like functionality for simple operations
    class BasicNP:
        @staticmethod
        def array(data):
            return list(data)
        
        @staticmethod
        def percentile(data, percent):
            sorted_data = sorted(data)
            index = int(len(sorted_data) * percent / 100)
            return sorted_data[min(index, len(sorted_data) - 1)]
        
        @staticmethod
        def arange(length):
            return list(range(length))
    
    np = BasicNP()


class AudioSynchronizer:
    """Advanced audio synchronization using speech pattern analysis"""
    
    def __init__(self, cache_dir=None):
        self.cache_dir = cache_dir or tempfile.gettempdir()
        self.cache_subdir = os.path.join(self.cache_dir, "audio_sync_cache")
        os.makedirs(self.cache_subdir, exist_ok=True)
        
        # Analysis parameters
        self.sample_rate = 22050
        self.hop_length = 512
        self.frame_length = 2048
        
    def _get_file_hash(self, file_path):
        """Generate hash for caching purposes"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read(8192)  # Read first 8KB for speed
                return hashlib.md5(content).hexdigest()[:16]
        except Exception:
            return None
    
    def _get_cache_path(self, file_hash, analysis_type):
        """Get cache file path for storing analysis results"""
        if not file_hash:
            return None
        cache_file = f"{file_hash}_{analysis_type}.pkl"
        return os.path.join(self.cache_subdir, cache_file)
    
    def _save_to_cache(self, cache_path, data):
        """Save analysis data to cache"""
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(data, f)
        except Exception as e:
            print(f"Cache save failed: {e}")
    
    def _load_from_cache(self, cache_path):
        """Load analysis data from cache"""
        try:
            if os.path.exists(cache_path):
                with open(cache_path, 'rb') as f:
                    return pickle.load(f)
        except Exception as e:
            print(f"Cache load failed: {e}")
        return None
    
    def extract_audio_for_analysis(self, video_path, output_path):
        """Extract audio from video for analysis"""
        try:
            cmd = [
                'ffmpeg', '-y', '-i', video_path,
                '-ar', str(self.sample_rate),
                '-ac', '1',  # Mono
                '-f', 'wav',
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"Audio extraction failed: {result.stderr}")
            
            return output_path
            
        except Exception as e:
            raise Exception(f"Failed to extract audio: {str(e)}")
    
    def analyze_speech_timing(self, audio_path, progress_callback=None):
        """
        Analyze speech timing patterns using available libraries
        
        Returns:
            dict: Contains speech segments, silence gaps, onset times, energy patterns
        """
        try:
            # Check cache first
            file_hash = self._get_file_hash(audio_path)
            cache_path = self._get_cache_path(file_hash, "speech_timing")
            
            if cache_path:
                cached_result = self._load_from_cache(cache_path)
                if cached_result is not None:
                    print("Using cached speech timing analysis")
                    if progress_callback:
                        progress_callback(100)
                    return cached_result
            
            print(f"Analyzing speech timing for: {audio_path}")
            
            if progress_callback:
                progress_callback(10)
            
            if ADVANCED_ANALYSIS_AVAILABLE:
                # Use librosa for advanced analysis
                return self._analyze_with_librosa(audio_path, progress_callback)
            else:
                # Use basic FFmpeg-based analysis
                return self._analyze_with_ffmpeg(audio_path, progress_callback)
                
        except Exception as e:
            raise Exception(f"Speech timing analysis failed: {str(e)}")
    
    def _analyze_with_librosa(self, audio_path, progress_callback=None):
        """Advanced analysis using librosa"""
        if not ADVANCED_ANALYSIS_AVAILABLE:
            raise Exception("Librosa not available")
        
        y, sr = librosa.load(audio_path, sr=self.sample_rate)
        duration = len(y) / sr
        
        if progress_callback:
            progress_callback(25)
        
        # Onset detection for word boundaries
        onset_frames = librosa.onset.onset_detect(
            y=y, sr=sr, 
            hop_length=self.hop_length,
            backtrack=True,
            units='time'
        )
        
        if progress_callback:
            progress_callback(40)
        
        # Energy analysis for speech/silence detection
        frame_length = self.frame_length
        hop_length = self.hop_length
        
        # RMS energy
        rms = librosa.feature.rms(
            y=y, 
            frame_length=frame_length, 
            hop_length=hop_length
        )[0]
        
        # Time axis for energy
        times = librosa.frames_to_time(
            np.arange(len(rms)), 
            sr=sr, 
            hop_length=hop_length
        )
        
        if progress_callback:
            progress_callback(60)
        
        # Speech/silence segmentation using energy threshold
        energy_threshold = np.percentile(rms, 25)  # Dynamic threshold
        speech_mask = rms > energy_threshold
        
        # Find speech segments
        speech_segments = []
        silence_segments = []
        
        in_speech = False
        segment_start = 0
        
        for i, is_speech in enumerate(speech_mask):
            time_pos = times[i]
            
            if is_speech and not in_speech:
                # Start of speech segment
                if segment_start < time_pos:
                    silence_segments.append((segment_start, time_pos))
                segment_start = time_pos
                in_speech = True
            elif not is_speech and in_speech:
                # End of speech segment
                speech_segments.append((segment_start, time_pos))
                segment_start = time_pos
                in_speech = False
        
        # Handle final segment
        if in_speech:
            speech_segments.append((segment_start, duration))
        else:
            silence_segments.append((segment_start, duration))
        
        if progress_callback:
            progress_callback(80)
        
        # Spectral features for speech quality analysis
        spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
        
        analysis_result = {
            'duration': duration,
            'onset_times': onset_frames.tolist(),
            'speech_segments': speech_segments,
            'silence_segments': silence_segments,
            'energy_profile': {
                'times': times.tolist(),
                'rms': rms.tolist(),
                'threshold': float(energy_threshold)
            },
            'spectral_features': {
                'centroids': spectral_centroids.tolist(),
                'rolloff': spectral_rolloff.tolist()
            },
            'sample_rate': sr,
            'analysis_method': 'librosa'
        }
        
        return analysis_result
    
    def _analyze_with_ffmpeg(self, audio_path, progress_callback=None):
        """Basic analysis using FFmpeg and simple techniques"""
        print("Using basic FFmpeg-based analysis")
        
        # Get audio duration
        duration = self._get_audio_duration(audio_path)
        
        if progress_callback:
            progress_callback(30)
        
        # Use FFmpeg to analyze audio levels for speech detection
        silence_detect_cmd = [
            'ffmpeg', '-i', audio_path,
            '-af', 'silencedetect=noise=-30dB:duration=0.5',
            '-f', 'null', '-'
        ]
        
        result = subprocess.run(silence_detect_cmd, capture_output=True, text=True)
        
        if progress_callback:
            progress_callback(60)
        
        # Parse silence detection output
        speech_segments = []
        silence_segments = []
        
        # Basic fallback if FFmpeg analysis fails
        if result.returncode != 0 or not result.stderr:
            # Create simple segments based on duration
            segment_duration = min(10.0, duration / 3)  # Max 10 second segments
            current_time = 0
            
            while current_time < duration:
                end_time = min(current_time + segment_duration, duration)
                speech_segments.append((current_time, end_time))
                current_time = end_time
                
                # Add small silence gap between segments
                if current_time < duration:
                    silence_end = min(current_time + 0.5, duration)
                    silence_segments.append((current_time, silence_end))
                    current_time = silence_end
        else:
            # Parse FFmpeg silence detection output
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
            
            # Build speech and silence segments
            current_pos = 0
            for i in range(len(silence_starts)):
                if silence_starts[i] > current_pos:
                    speech_segments.append((current_pos, silence_starts[i]))
                
                if i < len(silence_ends):
                    silence_segments.append((silence_starts[i], silence_ends[i]))
                    current_pos = silence_ends[i]
                else:
                    current_pos = silence_starts[i]
            
            # Add final speech segment if needed
            if current_pos < duration:
                speech_segments.append((current_pos, duration))
        
        if progress_callback:
            progress_callback(90)
        
        # Create simplified analysis result
        analysis_result = {
            'duration': duration,
            'onset_times': [seg[0] for seg in speech_segments],  # Use speech starts as onsets
            'speech_segments': speech_segments,
            'silence_segments': silence_segments,
            'energy_profile': {
                'times': [0, duration],
                'rms': [0.5, 0.5],  # Simplified
                'threshold': 0.25
            },
            'spectral_features': {
                'centroids': [1000.0] * len(speech_segments),  # Simplified
                'rolloff': [5000.0] * len(speech_segments)
            },
            'sample_rate': self.sample_rate,
            'analysis_method': 'ffmpeg_basic'
        }
        
        return analysis_result
    
    def _get_audio_duration(self, audio_path):
        """Get audio duration using FFprobe"""
        cmd = [
            'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
            '-of', 'csv=p=0', audio_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return float(result.stdout.strip())
        return 0
    
    def map_tts_to_original(self, original_patterns, tts_audio_path, progress_callback=None):
        """
        Map TTS audio timing to original speech patterns
        
        Args:
            original_patterns: Result from analyze_speech_timing
            tts_audio_path: Path to TTS audio file
            
        Returns:
            dict: Timing mapping for synchronization
        """
        try:
            print("Mapping TTS audio to original patterns")
            
            if progress_callback:
                progress_callback(10)
            
            # Analyze TTS audio with same method
            tts_patterns = self.analyze_speech_timing(tts_audio_path)
            
            if progress_callback:
                progress_callback(50)
            
            # Extract key timing information
            original_speech_segs = original_patterns['speech_segments']
            tts_speech_segs = tts_patterns['speech_segments']
            
            original_duration = original_patterns['duration']
            tts_duration = tts_patterns['duration']
            
            # Create segment mapping
            segment_mappings = []
            
            # Simple mapping strategy: pair segments by order and relative position
            for i, orig_seg in enumerate(original_speech_segs):
                if i < len(tts_speech_segs):
                    tts_seg = tts_speech_segs[i]
                    
                    # Calculate stretch factor for this segment
                    orig_seg_dur = orig_seg[1] - orig_seg[0]
                    tts_seg_dur = tts_seg[1] - tts_seg[0]
                    
                    if tts_seg_dur > 0:
                        stretch_factor = orig_seg_dur / tts_seg_dur
                    else:
                        stretch_factor = 1.0
                    
                    segment_mappings.append({
                        'original_segment': orig_seg,
                        'tts_segment': tts_seg,
                        'stretch_factor': stretch_factor,
                        'target_start': orig_seg[0],
                        'target_end': orig_seg[1]
                    })
            
            if progress_callback:
                progress_callback(80)
            
            # Global timing adjustment
            total_stretch = original_duration / tts_duration if tts_duration > 0 else 1.0
            
            timing_map = {
                'segment_mappings': segment_mappings,
                'global_stretch': total_stretch,
                'original_duration': original_duration,
                'tts_duration': tts_duration,
                'original_speech_segments': original_speech_segs,
                'tts_speech_segments': tts_speech_segs
            }
            
            if progress_callback:
                progress_callback(100)
            
            print(f"Timing mapping created: {len(segment_mappings)} segment pairs")
            return timing_map
            
        except Exception as e:
            raise Exception(f"TTS mapping failed: {str(e)}")
    
    def apply_timing_adjustments(self, tts_path, timing_map, output_path, progress_callback=None):
        """
        Apply timing adjustments to TTS audio using ffmpeg filters
        
        Args:
            tts_path: Input TTS audio path
            timing_map: Timing mapping from map_tts_to_original
            output_path: Output synchronized audio path
        """
        try:
            print("Applying timing adjustments to TTS audio")
            
            if progress_callback:
                progress_callback(10)
            
            # For complex timing adjustments, we'll use a simpler approach first
            # Apply global stretch factor with quality preservation
            global_stretch = timing_map['global_stretch']
            
            # Clamp stretch factor to reasonable bounds for quality
            stretch_factor = max(0.5, min(2.0, global_stretch))
            
            if progress_callback:
                progress_callback(30)
            
            # Use atempo filter for time stretching (preserves pitch)
            # atempo has range 0.5-2.0, so we may need to chain filters
            filters = []
            remaining_stretch = stretch_factor
            
            while remaining_stretch > 2.0:
                filters.append("atempo=2.0")
                remaining_stretch /= 2.0
            
            while remaining_stretch < 0.5:
                filters.append("atempo=0.5")
                remaining_stretch /= 0.5
            
            if remaining_stretch != 1.0:
                filters.append(f"atempo={remaining_stretch:.3f}")
            
            if progress_callback:
                progress_callback(60)
            
            # Build ffmpeg command
            if filters:
                filter_chain = ",".join(filters)
                cmd = [
                    'ffmpeg', '-y',
                    '-i', tts_path,
                    '-filter:a', filter_chain,
                    '-acodec', 'libmp3lame',
                    '-q:a', '2',  # High quality MP3
                    output_path
                ]
            else:
                # No adjustment needed, just copy
                cmd = [
                    'ffmpeg', '-y',
                    '-i', tts_path,
                    '-acodec', 'copy',
                    output_path
                ]
            
            if progress_callback:
                progress_callback(80)
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"FFmpeg timing adjustment failed: {result.stderr}")
            
            if progress_callback:
                progress_callback(100)
            
            print(f"Timing adjustment complete: stretch factor {stretch_factor:.3f}")
            return output_path
            
        except Exception as e:
            raise Exception(f"Timing adjustment failed: {str(e)}")
    
    def smart_sync(self, video_path, tts_audio_path, output_dir, progress_callback=None):
        """
        Main method that orchestrates the full smart synchronization process
        
        Args:
            video_path: Path to original video
            tts_audio_path: Path to TTS-generated audio
            output_dir: Directory for output files
            progress_callback: Function to report progress (0-100)
            
        Returns:
            str: Path to synchronized audio file
        """
        try:
            print("Starting smart audio synchronization")
            
            # Step 1: Extract audio from video (25%)
            if progress_callback:
                progress_callback(5)
            
            original_audio_path = os.path.join(output_dir, "original_audio.wav")
            self.extract_audio_for_analysis(video_path, original_audio_path)
            
            if progress_callback:
                progress_callback(25)
            
            # Step 2: Analyze original speech patterns (50%)
            def analysis_progress(p):
                if progress_callback:
                    progress_callback(25 + int(p * 0.25))
            
            original_patterns = self.analyze_speech_timing(original_audio_path, analysis_progress)
            
            if progress_callback:
                progress_callback(50)
            
            # Step 3: Map TTS to original patterns (75%)
            def mapping_progress(p):
                if progress_callback:
                    progress_callback(50 + int(p * 0.25))
            
            timing_map = self.map_tts_to_original(original_patterns, tts_audio_path, mapping_progress)
            
            if progress_callback:
                progress_callback(75)
            
            # Step 4: Apply timing adjustments (100%)
            def adjustment_progress(p):
                if progress_callback:
                    progress_callback(75 + int(p * 0.25))
            
            synchronized_audio_path = os.path.join(output_dir, "synchronized_tts_audio.mp3")
            result_path = self.apply_timing_adjustments(
                tts_audio_path, 
                timing_map, 
                synchronized_audio_path,
                adjustment_progress
            )
            
            if progress_callback:
                progress_callback(100)
            
            # Cleanup temporary files
            if os.path.exists(original_audio_path):
                os.remove(original_audio_path)
            
            print("Smart synchronization complete")
            return result_path
            
        except Exception as e:
            print(f"Smart sync failed: {str(e)}")
            raise Exception(f"Smart audio synchronization failed: {str(e)}")