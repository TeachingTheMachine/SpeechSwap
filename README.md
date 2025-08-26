# Video SpeechSwap 🎬

**Video SpeechSwap** is an AI-powered video processing application that transforms video content by replacing original audio with AI-generated text-to-speech while maintaining precise synchronization. This intelligent system delivers high-quality voice replacement with multiple synchronization methods for professional video editing needs.

## What It Solves 📝

Traditional video voice replacement requires expensive voice actors, time-consuming recording sessions, and complex audio editing to maintain lip synchronization. This system addresses these challenges by leveraging OpenAI's advanced TTS technology to create natural-sounding voice replacements with automated synchronization that matches video timing.

## How It Works 🤝

The system uses a streamlined processing pipeline:
- **Video Processing**: Extracts audio from uploaded video files and analyzes duration
- **Speech Transcription**: Uses OpenAI's Whisper API for accurate speech-to-text conversion
- **TTS Generation**: Creates new audio using OpenAI's TTS API with multiple voice options
- **Audio Synchronization**: Applies intelligent timing adjustments to match video duration perfectly

## Tech Stack 🛠️

Built with **Streamlit** for the web interface, powered by **OpenAI APIs** for transcription and TTS, with **FFmpeg** and **MoviePy** handling video/audio processing.

## Architecture 🏗️

Video SpeechSwap is built on a modular architecture designed for efficient video processing and audio synchronization.

### Core Components

**Frontend Layer**
- **Streamlit Web Interface**: Single-page application with intuitive file upload and processing controls
- **Session State Management**: Tracks processing status, temporary files, and user preferences
- **Interactive Controls**: Voice selection, speed adjustment, and synchronization method options

**Processing Pipeline**
- **VideoProcessor**: Handles video file operations, audio extraction, and transcript generation
- **SyncFirstTTS**: Pre-calculates optimal TTS speed for perfect timing without post-processing
- **AudioSynchronizer**: Advanced speech pattern analysis using librosa for precise timing
- **PauseSync**: Pause-aware audio stretching that analyzes silence gaps for better synchronization

**Audio Intelligence**
- **Multiple Sync Methods**: Sync-First (default), pause detection, basic stretching, and advanced pattern matching
- **Voice Customization**: Six OpenAI TTS voices (alloy, echo, fable, onyx, nova, shimmer)
- **Speed Control**: Adjustable speech rate from 0.25x to 4.0x for fine-tuning

### Data Flow
Video upload → Audio extraction → Whisper transcription → TTS generation with calculated speed → Audio synchronization → Final video assembly

## Processing Methods ⚙️

The system implements multiple synchronization approaches to ensure optimal audio-video alignment.

**Sync-First Method (Default)**
- **Mathematical Speed Calculation**: Pre-calculates exact TTS speed needed using formula: required_speed = (word_count ÷ 150 wpm) ÷ video_duration_minutes
- **Perfect Timing**: Generates audio at precise duration without post-processing
- **Fastest Processing**: Most efficient method with immediate results

**Enhanced Synchronization Options**
- **Pause Detection**: Analyzes silence gaps in original and TTS audio for segment-based stretching
- **Speech Pattern Analysis**: Uses librosa for advanced onset detection and timing alignment
- **Basic Stretching**: Simple tempo adjustment using FFmpeg's atempo filter

**Quality Assurance**
- **Duration Validation**: Ensures final video maintains original timing within milliseconds
- **Audio Quality**: Maintains high fidelity through intelligent processing methods
- **Error Handling**: Comprehensive fallback options for various video formats and edge cases

## Why It's Effective 🌟

- **AI-Powered Accuracy**: Uses OpenAI's state-of-the-art Whisper and TTS models for professional-quality transcription and voice generation
- **Perfect Synchronization**: Mathematical timing calculations ensure audio matches video duration precisely without manual adjustment
- **Multiple Voice Options**: Six distinct AI voices provide flexibility for different content types and audiences
- **Streamlined Workflow**: Complete processing from video upload to final output in a single interface

## Voice Quality & Limitations 🎯

**Current Voice Synchronization**
- **Timing Accuracy**: Excellent duration matching with mathematical precision
- **Audio Quality**: High-fidelity AI voices suitable for most content types
- **Lip Sync Limitation**: While timing is precise, lip movement synchronization is not perfect and represents an area for improvement

**We Welcome Contributors!**
The voice synchronization technology, while functional, could benefit from community contributions to improve lip-sync accuracy. Areas for enhancement include:
- Advanced phoneme-level timing analysis
- Improved speech pattern matching algorithms
- Real-time lip movement detection and adjustment
- Enhanced pause and breathing pattern recognition

## Customization Options 🛠️

**User Configuration**
- **Voice Selection**: Choose from six OpenAI TTS voices with distinct characteristics
- **Speed Control**: Adjust speech rate from 0.25x to 4.0x for perfect timing
- **Sync Methods**: Select from multiple synchronization approaches based on content needs
- **Format Support**: Works with MP4, AVI, MOV, MKV, and WebM video formats

**Technical Flexibility**
- **Modular Architecture**: Easy to extend with additional synchronization methods
- **API Integration**: Built for potential integration with other video processing tools
- **Open Source Opportunity**: Codebase ready for community contributions and enhancements

The system provides both immediate usability for content creators and a foundation for developers interested in advancing AI-powered video processing technology.

## Getting Started 🚀

1. **Upload Video**: Select your video file (MP4, AVI, MOV, MKV, WebM)
2. **Enter Text**: Paste the text you want as the new audio
3. **Choose Voice**: Select from six AI voices
4. **Adjust Settings**: Set speed and synchronization method
5. **Process**: Click "Start Processing" for automated conversion
6. **Download**: Get your video with replaced audio

## Contributing 🤝

We encourage contributions, especially in improving voice synchronization accuracy. The project would benefit from expertise in:
- Audio signal processing
- Lip synchronization algorithms
- Speech timing analysis
- Video processing optimization

Join us in making Video SpeechSwap the best AI-powered voice replacement tool available!