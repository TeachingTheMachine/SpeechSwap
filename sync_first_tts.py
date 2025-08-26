"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                              sync_first_tts.py                              ║
║                                                                              ║
║  Author: Replit AI Assistant                                                 ║
║  Date Created: August 26, 2025                                              ║
║  Purpose: Sync-First TTS generation with pre-calculated speed               ║
║  Description: Calculate exact TTS speed needed to match video duration      ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import re
from openai import OpenAI


class SyncFirstTTS:
    """Generate TTS audio at exactly the right speed to match video duration"""
    
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)
        self.base_speaking_rate = 150  # words per minute (standard rate)
        self.speed_buffer = 0.97  # Generate 3% shorter to avoid overrun
        self.min_speed = 0.25  # OpenAI's minimum speed
        self.max_speed = 4.0   # OpenAI's maximum speed
    
    def count_words(self, text):
        """Count words in text for duration estimation"""
        # Remove extra whitespace and split by whitespace
        words = re.findall(r'\b\w+\b', text.lower())
        return len(words)
    
    def estimate_natural_duration(self, text):
        """Estimate how long TTS would take at normal speed"""
        word_count = self.count_words(text)
        # Convert words per minute to seconds
        estimated_seconds = (word_count / self.base_speaking_rate) * 60
        return estimated_seconds
    
    def calculate_required_speed(self, text, target_duration):
        """Calculate the exact TTS speed needed to match target duration"""
        natural_duration = self.estimate_natural_duration(text)
        
        if natural_duration <= 0:
            return 1.0
        
        # Calculate raw speed needed
        raw_speed = natural_duration / target_duration
        
        # Apply buffer to make it slightly shorter
        buffered_speed = raw_speed / self.speed_buffer
        
        # Clamp to OpenAI's speed limits
        final_speed = max(self.min_speed, min(self.max_speed, buffered_speed))
        
        print(f"Text analysis:")
        print(f"  Words: {self.count_words(text)}")
        print(f"  Natural duration: {natural_duration:.1f}s")
        print(f"  Target duration: {target_duration:.1f}s")
        print(f"  Raw speed needed: {raw_speed:.2f}x")
        print(f"  Buffered speed: {buffered_speed:.2f}x")
        print(f"  Final speed (clamped): {final_speed:.2f}x")
        
        return final_speed
    
    def generate_sync_first_tts(self, text, target_duration, voice="alloy", output_path=None):
        """
        Generate TTS audio at exactly the right speed to match target duration
        
        Args:
            text: Text to convert to speech
            target_duration: Target duration in seconds
            voice: OpenAI voice to use
            output_path: Output file path
            
        Returns:
            tuple: (output_path, actual_speed_used)
        """
        try:
            # Calculate the exact speed needed
            required_speed = self.calculate_required_speed(text, target_duration)
            
            print(f"Generating TTS at {required_speed:.2f}x speed for {target_duration:.1f}s target")
            
            # Generate TTS with calculated speed
            response = self.client.audio.speech.create(
                model="tts-1",  # the newest OpenAI model is "gpt-5" which was released August 7, 2025. do not change this unless explicitly requested by the user
                voice=voice,
                input=text,
                speed=required_speed
            )
            
            # Save to file
            if output_path is None:
                output_path = "sync_first_audio.mp3"
            
            with open(output_path, "wb") as f:
                f.write(response.content)
            
            print(f"Sync-first TTS generated successfully: {output_path}")
            print(f"Speed used: {required_speed:.2f}x")
            
            return output_path, required_speed
            
        except Exception as e:
            raise Exception(f"Sync-first TTS generation failed: {str(e)}")
    
    def get_speed_info(self, text, target_duration):
        """Get information about speed calculation without generating audio"""
        required_speed = self.calculate_required_speed(text, target_duration)
        
        word_count = self.count_words(text)
        natural_duration = self.estimate_natural_duration(text)
        
        # Check if speed is within acceptable limits
        is_feasible = self.min_speed <= required_speed <= self.max_speed
        
        return {
            'word_count': word_count,
            'natural_duration': natural_duration,
            'target_duration': target_duration,
            'required_speed': required_speed,
            'is_feasible': is_feasible,
            'speed_limit_hit': required_speed < self.min_speed or required_speed > self.max_speed,
            'recommendation': self._get_recommendation(required_speed)
        }
    
    def _get_recommendation(self, speed):
        """Get recommendation based on required speed"""
        if speed < self.min_speed:
            return f"Text is too short for video duration. Consider adding more content or using a shorter video."
        elif speed > self.max_speed:
            return f"Text is too long for video duration. Consider shortening text or using a longer video."
        elif speed > 2.0:
            return f"Speed is high ({speed:.1f}x) - audio may sound rushed."
        elif speed < 0.5:
            return f"Speed is very slow ({speed:.1f}x) - audio may sound unnatural."
        else:
            return f"Speed looks good ({speed:.1f}x) - should produce natural-sounding audio."