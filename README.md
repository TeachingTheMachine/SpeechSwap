# Video SpeechSwap 🎬

> **Note: Audio synchronization is functional but not perfect - lip sync accuracy could be improved and we welcome contributors to help solve this challenge.**

**Video SpeechSwap** is an AI-powered video audio replacement system that transforms any video by swapping out the original audio with crystal-clear AI-generated speech. Originally built by someone who got tired of rewind tech videos becuase of my own inability to filter through accents (no offense to anyone - accents are beautiful! Some just throw my brain for a loop.), this application creates semi- synchronized videos with narration to help with clarity and understanding.

## What It Solves 📝

Ever tried learning React from a tutorial where you spent more time rewinding than coding? Or attempted to follow along with a Python guide and that made you question your entire programming career? This system tackles the universal developer struggle of accent barriers in technical content. Whether you're wrestling with pronunciation mysteries in educational videos, dealing with audio that sounds like it was recorded in a wind tunnel, or just need clearer speech for better learning absorption, Video SpeechSwap turns "what did they just say?" moments into "oh, that actually makes sense!" experiences.

## How It Works 🤝

The system uses a surprisingly sophisticated pipeline to work its audio magic:
- **Video Intake**: Accepts your uploaded victims (video files) or YouTube URLs for processing
- **Text Wrangling**: Primarily relies on you pasting text (because let's be honest, auto-transcription is still playing catch-up), with backup options for YouTube transcript extraction when you're feeling lazy
- **Voice Wizardry**: Transforms text into remarkably human-sounding speech using OpenAI's TTS API with 6 voice personalities
- **Sync Sorcery**: Attempts to match audio timing with multiple methods (spoiler: it's harder than it looks, hence the contributor plea above)
- **Final Assembly**: Marries your original video with the new audio track, hopefully without too much drama


## Tech Stack 🛠️

Built with **Streamlit** because life's too short for complex frontend frameworks, **OpenAI TTS API** for the voice magic, **YouTubeTranscriptApi** for when we need to extract existing captions, **yt-dlp** for video downloads (the hero we don't deserve), **FFmpeg** for the heavy video lifting, and **Librosa** for pretending we understand advanced audio analysis.

## Architecture 🏗️

The Video SpeechSwap system follows a "let's make this work without breaking everything" architecture, designed for practical audio replacement with a side of optimistic synchronization.

### Core Components

**The "Please Work" Interface Layer**
- **Streamlit Web App**: Clean interface that doesn't require a PhD in web development to use
- **Session State Juggling**: Keeps track of where you are in the process without losing your mind or your files
- **Voice Personality Selector**: 6 OpenAI voices ranging from "professional narrator" to "that person who sounds way smarter than you"
- **Speed Controls**: Because sometimes you need your AI narrator to slow down or speak like they've had too much coffee

**The "Trust Me, I Know What I'm Doing" Text Engine**
- **Manual Text Input**: The star of the show - paste your text and let the magic happen
- **YouTube Transcript Rescue Mission**: Falls back to extracting captions when available (uses YouTubeTranscriptApi, Google OAuth, and yt-dlp because redundancy is survival)
- **Text Cleaning Service**: Removes weird characters and formatting that make TTS sound like it's having an existential crisis
- **Multi-API Safety Net**: Because if one method fails, we've got backups for our backups

**The "Heavy Lifting" Video Engine**
- **VideoProcessor Class**: The workhorse that handles video downloads and audio extraction without complaining
- **Format Tolerance**: Accepts MP4, AVI, MOV, MKV, WebM - basically everything except that one weird format your friend always uses
- **Duration Detective**: Figures out exact video timing for sync calculations (this part actually works well)
- **Audio Extraction**: Cleanly separates audio tracks like a surgical precision tool, if surgery involved FFmpeg

**The "Voice Actor in a Box" AI Layer**
- **OpenAI TTS Integration**: Six professionally-trained AI voices that sound better than most of us on Monday mornings
- **SyncFirstTTS**: The "measure twice, cut once" approach - calculates perfect speed before generating audio
- **BasicTTSGenerator**: Handles standard voice generation with customizable personality and speed
- **Audio Analysis**: Uses PyDub to detect pauses and silence (surprisingly philosophical when you think about it)

**The "Cross Your Fingers" Synchronization Systems**
*(These work... most of the time... we're working on it)*
1. **Sync-First Method**: Pre-calculates TTS speed to match video - like GPS for audio timing
2. **Pause Analysis**: Detects silence gaps and tries to match them (results may vary, like horoscopes)
3. **Smart Sync**: Uses Librosa for "advanced" audio analysis (translation: lots of math we hope works)
4. **Enhanced Stretch**: Time-stretches audio while trying to preserve natural speech patterns
5. **Basic Methods**: When all else fails, loop it, fade it, or just give up gracefully

### Data Flow
Video upload → Manual text paste (or transcript extraction for the brave) → TTS generation with timing wizardry → Synchronization attempts → Final video assembly → Cross fingers and download

## AgentOps ⚙️

The system implements operations that would make a production engineer slightly nervous but ultimately impressed.

**The "Are We There Yet?" Pipeline**
- **Progress Bars**: Visual feedback so you know the system hasn't given up on life
- **Error Gracefully Handling**: When things go wrong (and they sometimes do), the system fails upward with helpful messages
- **Temporary File Babysitting**: Creates files, uses files, cleans up files, repeat (with the dedication of a responsible pet owner)

**The "Voice Acting Academy" Operations**
- **OpenAI API Whispering**: Direct communication with OpenAI's TTS models (they're surprisingly good listeners)
- **Speed Calculation Magic**: Determines optimal speech speed based on text length and video duration
- **Quality Control**: Text preprocessing that removes the stuff that makes AI voices sound like robots having a breakdown
- **Voice Variety Show**: Six distinct personalities for when you can't decide if you want to sound authoritative or approachable

**The "Timing is Everything" Synchronization** *(Contributors Desperately Wanted)*
- **Multi-Method Madness**: Tries different sync approaches until something works acceptably well
- **Duration Matching Attempts**: Math-heavy processes that sometimes produce beautiful results
- **Audio Analysis**: Uses legitimate signal processing (PyDub and Librosa) to understand speech patterns
- **Quality vs. Time Trade-offs**: Fast processing or good sync - pick one (we're working on having both)

**The "File Wrangling Rodeo" Operations**
- **Video Download Service**: Grabs YouTube videos with the determination of a motivated intern
- **Audio Extraction Precision**: Separates audio from video cleaner than most breakups
- **Format Conversion Diplomacy**: Handles multiple formats without starting international incidents
- **Output Assembly Line**: Puts everything back together like video Humpty Dumpty

## Why It's Effective 🌟

- **Real-World Problem Solving**: Born from the frustration of "I just want to understand this Python tutorial without rewinding 47 times"
- **Practical Over Perfect**: Prioritizes functional results over theoretical perfection (though we're working on both)
- **Voice Variety**: Six AI personalities because everyone learns differently, and some of us prefer narrators who don't sound like they're reading a phone book
- **Manual Text Power**: Complete control over output means no "the AI thought they said 'duck' when they clearly meant 'dock'" situations
- **Educational Focus**: Specifically designed for making coding tutorials, tech talks, and educational content more accessible to human ears

*Disclaimer: While the audio will sound professional and clear, the lip sync might occasionally give your videos a "poorly dubbed martial arts movie" vibe. We're embracing this as a feature while secretly working on a fix.*

## Customization Options 🛠️

**The "Make It Your Own" Self-Service Menu**
- **Voice Casting**: Choose from 6 AI voice actors who never demand overtime pay or artistic creative control
- **Speed Dial**: Adjust speech from "meditation guru" (0.25x) to "auctioneer having a panic attack" (4.0x)
- **Sync Strategy Selection**: Pick your synchronization poison based on how much you trust our algorithms
- **Text Liberation**: Complete freedom through manual input - no AI trying to guess what humans actually said

**The "Under the Hood" Technical Tweaking**
- **Sync Algorithm Surgery**: Modify timing calculations, pause detection, and stretch ratios (warranty void if you break anything)
- **Audio Processing Philosophy**: Adjust how the system thinks about silence, speech, and the meaning of existence
- **Transcript Extraction Hierarchy**: Configure which backup methods kick in when the primary approach has an existential crisis
- **Output Quality Negotiations**: Balance file size, processing time, and video quality like a diplomatic summit

**The "Please Help Us" Contributor Wishlist** 🤝
- **Lip Sync Enlightenment**: We need someone who understands the dark arts of visual-audio alignment
- **Timing Analysis Wizardry**: Advanced speech pattern matching that actually works consistently
- **Pause Detection Mastery**: Better silence boundary detection (harder than it sounds, no pun intended)
- **Sync Quality Metrics**: Tools to measure just how off our timing really is (ignorance was bliss)

**Professional "We'll Do It For You" Services**
- **Custom Algorithm Development**: Specialized sync solutions for when you need better than "pretty good"
- **Batch Processing Systems**: For when you have 200 videos and a deadline
- **Enterprise Integration**: Making this work with your existing video workflows without breaking everything
- **Quality Enhancement Suite**: Additional audio processing that makes everything sound even more professional

The system delivers immediate value for anyone who's ever wished technical content came with subtitles for their ears, while providing endless opportunities for community improvement (especially if you know more about audio synchronization than we do).