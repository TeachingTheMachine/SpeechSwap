# Video SpeechSwap 🎬
*Results: Professional audio quality with functional synchronization. Lip sync accuracy is limited and requires improvement.*

> **Note: Audio synchronization is functional but not perfect - lip sync accuracy could be improved and we welcome contributors to help solve this challenge.**

**Video SpeechSwap** is an AI-powered video audio replacement system that transforms any video by replacing the original audio with clear AI-generated speech. Originally built to address comprehension challenges with accented speech in coding tutorials, this application creates synchronized videos with professional narration for improved accessibility and understand.

## What It Solves 📝

This system addresses comprehension challenges in technical content where accent barriers, poor audio quality, or unclear speech patterns impede learning. Video SpeechSwap replaces original audio with clear, standardized narration, making educational content more accessible for effective learning.

## How It Works 🤝

The system uses a multi-step pipeline for audio replacement:
- **Video Input**: Accepts uploaded video files or YouTube URLs for processing
- **Text Processing**: Primarily uses manual text input, with fallback options for YouTube transcript extraction
- **Voice Generation**: Converts text to speech using OpenAI's TTS API with 6 voice options
- **Audio Synchronization**: Applies timing algorithms to match audio duration with video length
- **Final Assembly**: Combines original video with synchronized AI-generated audio



## Tech Stack 🛠️

Built with **Streamlit** for the web interface, **OpenAI TTS API** for voice generation, **YouTubeTranscriptApi** for caption extraction, **yt-dlp** for video downloads, **FFmpeg** for video processing, and **Librosa** for audio analysis.

## Requirements 📋

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt
```

### Dependencies (requirements.txt)
```
streamlit>=1.48.1
yt-dlp>=2025.8.20
youtube-transcript-api>=3.2.1
openai>=1.0.0
ffmpeg-python>=0.2.0
moviepy>=2.2.1
pydub>=0.25.1
librosa>=0.10.0
google-auth-oauthlib>=1.0.0
google-api-python-client>=2.0.0
google-auth>=2.0.0
numpy>=1.21.0
requests>=2.25.0
```

### System Requirements
- **Python**: 3.11 or higher
- **FFmpeg**: Required for video/audio processing (install via system package manager)
- **IDE**: Any Python IDE (VS Code, PyCharm, etc.) or run directly with Streamlit
- **Memory**: 4GB+ recommended for video processing
- **Storage**: Temporary space for video files during processing

### API Requirements
- **OpenAI API Key**: Required for TTS generation
  - Set as environment variable: `OPENAI_API_KEY=your_key_here`
  - Cost: ~$15 per 1 million characters (very affordable for TTS)
- **YouTube API Key** (Optional): For transcript extraction fallback
  - Set as environment variable: `YOUTUBE_API_KEY=your_key_here` 
- **Google OAuth Credentials** (Optional): For advanced YouTube transcript access
  - Set as environment variable: `GOOGLE_OAUTH_CREDENTIALS_JSON=your_credentials_json`

### Installation Notes
```bash
# On Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg

# On macOS
brew install ffmpeg

# On Windows
# Download FFmpeg from https://ffmpeg.org/download.html
# Add to system PATH
```

## Architecture 🏗️

The Video SpeechSwap system follows a modular architecture designed for practical audio replacement.

### Core Components

**Web Interface Layer**
- **Streamlit Application**: Web interface with progress tracking and file management
- **Session State Management**: Handles processing status and temporary file cleanup  
- **Voice Controls**: 6 OpenAI TTS voice options with speed adjustment (0.25x to 4.0x)
- **Sync Method Selection**: Multiple synchronization approaches for different content types

**Text Processing Engine**
- **Manual Text Input**: Primary method - users provide text for voice generation
- **YouTube Transcript Extraction**: Fallback system using YouTubeTranscriptApi, Google OAuth, and yt-dlp
- **Text Cleaning**: Removes problematic characters and formatting for optimal TTS output
- **Multi-API Fallback**: Robust transcript extraction with multiple backup methods

**Video Processing Engine**
- **VideoProcessor**: Handles video downloads and audio extraction using FFmpeg
- **Format Support**: Compatible with MP4, AVI, MOV, MKV, and WebM video formats
- **Duration Analysis**: Precise timing calculation for synchronization methods
- **Audio Extraction**: Clean separation of original audio tracks for analysis

**AI Voice Generation Layer**
- **OpenAI TTS Integration**: Six professionally-trained AI voices for different speaking styles
- **SyncFirstTTS**: Pre-calculates optimal TTS speed to match video duration
- **BasicTTSGenerator**: Handles standard voice generation with speed and voice customization
- **Audio Analysis**: Uses PyDub for silence detection and audio manipulation

**Audio Synchronization Systems** *(Functional but seeking improvement)*
1. **Sync-First Method**: Pre-calculates TTS speed to match video duration
2. **Pause Analysis**: Detects silence gaps and attempts timing alignment
3. **Smart Sync**: Uses Librosa for audio analysis and speech pattern matching
4. **Enhanced Stretch**: Time-stretches audio while preserving natural speech patterns
5. **Basic Methods**: Simple loop, fade, and duration-matching approaches

### Data Flow
Video upload → Manual text input (or transcript extraction) → TTS generation with timing calculation → Synchronization processing → Final video assembly → Download

## AgentOps ⚙️

The system implements comprehensive processing operations for reliable video transformations.

**Processing Pipeline Management**
- **Progress Tracking**: Real-time visual progress with detailed status updates
- **Error Handling**: Robust fallback mechanisms between different methods and API endpoints
- **File Management**: Automatic cleanup of temporary files with secure handling

**Text-to-Speech Operations**
- **OpenAI API Integration**: Direct API communication with OpenAI's TTS models
- **Speed Optimization**: Dynamic speed calculation based on text length and target duration
- **Quality Processing**: Text preprocessing and cleaning for optimal TTS output
- **Voice Options**: Six distinct voices with different characteristics and speaking styles

**Synchronization Processing** *(Seeking improvement from contributors)*
- **Multi-Method Approach**: Multiple sync strategies with intelligent fallbacks
- **Duration Matching**: Timing analysis and adjustment algorithms
- **Audio Analysis**: Signal processing using PyDub and Librosa for speech pattern detection
- **Quality Trade-offs**: Balance between processing speed and synchronization accuracy

**Media Processing Operations**
- **Video Download**: YouTube video acquisition with error handling
- **Audio Extraction**: Clean audio track separation using FFmpeg and MoviePy
- **Format Handling**: Multiple video and audio format support with automatic conversion
- **Output Assembly**: Final video compilation with quality optimization

## Why It's Effective 🌟

- **Practical Solution**: Addresses real comprehension barriers in technical content
- **Manual Control**: Primary focus on user-provided text eliminates transcription errors
- **Voice Options**: Six professional AI voices for different learning preferences  
- **Educational Focus**: Optimized for coding tutorials and technical educational content
- **Accessibility**: Makes technical content more accessible regardless of original audio quality

*Note: Audio quality is professional and clear. Synchronization is functional but lip sync accuracy remains limited.*

## Customization Options 🛠️

**Self-Service Configuration**
- **Voice Selection**: Choose from 6 AI voices with distinct characteristics and speaking styles
- **Speed Control**: Adjust speech rate from 0.25x to 4.0x for optimal comprehension
- **Sync Strategy**: Select synchronization method based on content type and quality requirements
- **Text Input**: Complete control through manual text input rather than auto-transcription

**Technical Configuration**
- **Sync Algorithm Adjustment**: Modify timing calculations, pause detection thresholds, and stretch ratios
- **Audio Processing**: Configure silence detection parameters and speech analysis settings  
- **Transcript Extraction**: Set API preferences and fallback method priorities
- **Output Settings**: Customize video encoding parameters and quality settings

**Areas Seeking Contributors** 🤝
- **Lip Sync Improvement**: Advanced visual-audio alignment algorithms
- **Timing Analysis**: Enhanced speech pattern matching and synchronization accuracy
- **Pause Detection**: Better silence boundary detection and speech segmentation
- **Sync Quality Metrics**: Tools to measure and improve timing accuracy

**Professional Services**
- **Custom Algorithm Development**: Specialized sync solutions for specific requirements
- **Batch Processing**: Automated processing systems for large video collections
- **Enterprise Integration**: Integration with existing video workflows and systems
- **Quality Enhancement**: Additional audio processing and optimization features

The system provides practical value for making technical content more accessible while offering opportunities for community improvement in synchronization accuracy.