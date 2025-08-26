# Overview

This is a YouTube Voice Replacement application built with Streamlit that allows users to replace the original audio in YouTube videos with AI-generated text-to-speech (TTS) audio. The application downloads YouTube videos, extracts their audio, transcribes the speech to text using OpenAI's Whisper API, and then generates new speech using OpenAI's TTS API with selectable voices. The final output is a video with the original visuals but replaced audio that maintains synchronization.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
- **Streamlit Web Interface**: Single-page application with a clean, intuitive UI
- **Session State Management**: Uses Streamlit's session state to track processing status, output paths, and temporary directories
- **Interactive Controls**: Sidebar with voice selection dropdown and speed adjustment controls
- **File Upload/URL Input**: Supports both YouTube URL input and direct video file uploads

## Backend Architecture
- **Modular Component Design**: Separated into distinct classes for different responsibilities:
  - `VideoProcessor`: Handles YouTube video downloading and video file operations
  - `AudioUtils`: Manages audio extraction from videos and transcription
  - `TTSGenerator`: Handles text-to-speech generation with voice customization
  - `AudioSynchronizer`: Advanced speech pattern analysis for lip sync using librosa
  - `PauseSync`: Pause-based audio synchronization analyzing silence gaps in both audio files
- **Temporary File Management**: Uses Python's `tempfile` module with automatic cleanup functionality
- **Error Handling**: Comprehensive exception handling with user-friendly error messages

## Processing Pipeline
- **Video Acquisition**: Downloads YouTube videos using `pytube` or accepts uploaded files
- **Audio Extraction**: Uses `moviepy` to separate audio tracks from video files
- **Speech Transcription**: Leverages OpenAI's Whisper API for accurate speech-to-text conversion
- **TTS Generation**: Generates new audio using OpenAI's TTS API with multiple voice options
- **Audio Synchronization**: Multiple methods available:
  - **Sync-First** (Default): Pre-calculates exact TTS speed needed to match video duration, generates perfect timing without post-processing
  - **Pause Analysis**: Analyzes silence gaps in both original and TTS audio, stretches speech segments to match timing precisely
  - **Smart Sync**: Uses librosa for advanced speech pattern analysis and onset detection
  - **Basic Methods**: Stretch, loop, fade options for simpler synchronization
- **Final Assembly**: Combines original video with synchronized TTS audio using FFmpeg

## Data Flow
1. User inputs YouTube URL or uploads video file
2. Video downloaded/processed and audio extracted
3. Audio transcribed to text using Whisper API
4. Text converted to speech using TTS API with selected voice and speed
5. New audio synchronized and combined with original video
6. Final processed video made available for download

# External Dependencies

## Core Libraries
- **Streamlit**: Web application framework for the user interface
- **MoviePy**: Video and audio processing, editing, and manipulation
- **PyTube**: YouTube video downloading functionality
- **PyDub**: Audio file format conversion and processing

## AI/ML Services
- **OpenAI API**: 
  - Whisper API for speech-to-text transcription
  - TTS API for text-to-speech generation with multiple voice options
- **API Authentication**: Requires OPENAI_API_KEY environment variable

## Audio Analysis Libraries
- **Librosa**: Advanced audio analysis for speech pattern detection and timing analysis
- **NumPy**: Numerical computing for audio signal processing and analysis
- **AudioSynchronizer**: Custom smart sync system for speech pattern matching

## Media Processing
- **FFmpeg**: Required by MoviePy for video/audio encoding and decoding operations
- **Audio Codecs**: Support for various audio formats (WAV, MP3, etc.)
- **Video Codecs**: Support for multiple video formats (MP4, AVI, MOV, MKV, WebM)

## System Requirements
- **Temporary Storage**: Local file system access for processing temporary files
- **Network Access**: Required for YouTube video downloads and OpenAI API calls
- **Memory Management**: Handles video processing in memory with cleanup routines
- **Caching System**: Stores audio analysis results to avoid re-processing identical videos