"""
Author: Vanessa Crosby
Date: August 23, 2025
File: app.py
Summary: Main Streamlit application for YouTube voice replacement with TTS
"""

import streamlit as st
import os
import tempfile
import shutil
from pathlib import Path
import traceback

from video_processor import VideoProcessor
from audio_utils import AudioUtils
from tts_generator import TTSGenerator

# Configure page
st.set_page_config(
    page_title="YouTube Voice Replacement",
    page_icon="🎬",
    layout="wide"
)

# Initialize session state
if 'processing_complete' not in st.session_state:
    st.session_state.processing_complete = False
if 'output_video_path' not in st.session_state:
    st.session_state.output_video_path = None
if 'temp_dir' not in st.session_state:
    st.session_state.temp_dir = None
if 'transcript_only_mode' not in st.session_state:
    st.session_state.transcript_only_mode = False

def cleanup_temp_files():
    """Clean up temporary files"""
    if st.session_state.temp_dir and os.path.exists(st.session_state.temp_dir):
        shutil.rmtree(st.session_state.temp_dir, ignore_errors=True)
        st.session_state.temp_dir = None

def main():
    st.title("🎬 YouTube Voice Replacement")
    st.markdown("""
    Replace YouTube video audio with clear TTS-generated speech while maintaining video synchronization.

    **New Feature**: Extract transcripts directly from YouTube without downloading videos!
    """)

    # Sidebar for settings
    st.sidebar.header("Settings")

    # TTS Voice selection
    voice_options = {
        "en-US-Standard-A": "Female voice (US English)",
        "en-US-Standard-B": "Male voice (US English)", 
        "en-US-Standard-C": "Female voice (US English)",
        "en-US-Standard-D": "Male voice (US English)",
        "en-US-Neural2-A": "Neural Female voice (US English)",
        "en-US-Neural2-C": "Neural Female voice (US English)",
        "en-US-Neural2-D": "Neural Male voice (US English)",
        "en-US-Neural2-F": "Neural Female voice (US English)"
    }

    tts_voice = st.sidebar.selectbox(
        "Select TTS Voice",
        options=list(voice_options.keys()),
        format_func=lambda x: voice_options[x],
        index=0,
        help="Choose the voice for text-to-speech conversion"
    )

    # Speed adjustment
    speech_speed = st.sidebar.slider(
        "Speech Speed",
        min_value=0.5,
        max_value=2.0,
        value=1.0,
        step=0.1,
        help="Adjust the speed of the generated speech"
    )

    # Processing mode selection
    st.sidebar.header("Processing Mode")
    transcript_only = st.sidebar.checkbox(
        "Transcript-only mode",
        value=True,
        help="Extract transcript from YouTube directly (faster, more reliable)"
    )

    if transcript_only:
        st.sidebar.info("💡 This mode extracts YouTube transcripts directly without downloading videos. Perfect for creating audio-only content!")

    # Main content area
    col1, col2 = st.columns([2, 1])

    with col1:
        st.header("Input")

        # Input method selection
        if transcript_only:
            st.info("🚀 **Transcript-only mode**: Only YouTube URLs supported in this mode")
            input_method = "YouTube URL"
        else:
            input_method = st.radio(
                "Choose input method:",
                ["YouTube URL", "Upload Video File"],
                horizontal=True
            )

        video_source = None

        if input_method == "YouTube URL":
            youtube_url = st.text_input(
                "Enter YouTube URL:",
                placeholder="https://www.youtube.com/watch?v=..."
            )
            if youtube_url:
                video_source = {"type": "youtube", "url": youtube_url, "transcript_only": transcript_only}

        elif not transcript_only:
            uploaded_file = st.file_uploader(
                "Upload video file",
                type=['mp4', 'avi', 'mov', 'mkv', 'webm'],
                help="Supported formats: MP4, AVI, MOV, MKV, WEBM"
            )
            if uploaded_file:
                video_source = {"type": "upload", "file": uploaded_file, "transcript_only": False}

    with col2:
        st.header("Process")

        if video_source:
            if st.button("🚀 Start Processing", type="primary", use_container_width=True):
                process_video(video_source, tts_voice, speech_speed)

        if st.session_state.processing_complete and st.session_state.output_video_path:
            st.success("✅ Processing Complete!")

            # Determine download button text and mime type
            if st.session_state.transcript_only_mode:
                download_text = "📥 Download Generated Audio"
                filename = "generated_audio.mp3"
                mime_type = "audio/mp3"
            else:
                download_text = "📥 Download Processed Video"
                filename = "processed_video.mp4"
                mime_type = "video/mp4"

            # Download button
            if os.path.exists(st.session_state.output_video_path):
                with open(st.session_state.output_video_path, "rb") as file:
                    st.download_button(
                        download_text,
                        data=file.read(),
                        file_name=filename,
                        mime=mime_type,
                        use_container_width=True
                    )

        # Reset button
        if st.button("🔄 Reset", use_container_width=True):
            cleanup_temp_files()
            st.session_state.processing_complete = False
            st.session_state.output_video_path = None
            st.session_state.transcript_only_mode = False
            st.rerun()

def process_video(video_source, tts_voice, speech_speed):
    """Process the video with progress tracking"""

    # Check for Google Cloud authentication
    try:
        test_tts = TTSGenerator()
        if not video_source.get("transcript_only", False):
            test_audio = AudioUtils()
    except Exception as e:
        st.error(f"❌ Google Cloud authentication failed: {str(e)}")
        st.info("""💡 **To set up Google Cloud authentication:**

        1. Create a Google Cloud project
        2. Enable Text-to-Speech API and Speech-to-Text API
        3. Create a service account and download the JSON key file
        4. Set the GOOGLE_APPLICATION_CREDENTIALS environment variable to point to your key file

        Or use gcloud CLI: `gcloud auth application-default login`

        **Free tier includes:**
        - Text-to-Speech: 4 million characters per month
        - Speech-to-Text: 60 minutes per month
        """)
        return

    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    st.session_state.temp_dir = temp_dir
    st.session_state.transcript_only_mode = video_source.get("transcript_only", False)

    # Progress tracking
    progress_container = st.container()

    try:
        # Initialize processors
        video_processor = VideoProcessor()
        audio_utils = AudioUtils()
        tts_generator = TTSGenerator()

        with progress_container:
            if video_source.get("transcript_only", False):
                # TRANSCRIPT-ONLY WORKFLOW
                st.info("🔄 Step 1: Extracting transcript from YouTube...")
                progress_bar = st.progress(0)

                # Get transcript directly
                transcript = video_processor.get_youtube_transcript(video_source["url"])
                progress_bar.progress(50)
                st.success("✅ Transcript extracted successfully")

                # Display transcript preview
                with st.expander("📝 Extracted Transcript", expanded=True):
                    st.text_area("Transcript", transcript, height=200, disabled=True)
                    st.info(f"📊 **Transcript Stats:** {len(transcript)} characters, ~{len(transcript.split())} words")

                # Generate TTS audio directly
                st.info("🔄 Step 2: Generating TTS audio...")
                tts_audio_path = tts_generator.generate_speech(
                    transcript, 
                    temp_dir, 
                    voice=tts_voice,
                    speed=speech_speed
                )
                progress_bar.progress(100)
                st.success("✅ Audio generation complete!")

                # Store result (in transcript-only mode, output is just the audio file)
                st.session_state.output_video_path = tts_audio_path
                st.session_state.processing_complete = True

                # Preview generated audio
                with st.expander("🔊 Preview Generated Audio", expanded=True):
                    if os.path.exists(tts_audio_path):
                        st.audio(tts_audio_path, format='audio/mp3')

                        # Show audio stats
                        audio_duration = audio_utils.get_audio_duration(tts_audio_path)
                        st.info(f"🎵 **Generated Audio:** {audio_duration:.1f} seconds duration")

            else:
                # FULL VIDEO PROCESSING WORKFLOW
                # Step 1: Download/Load video
                st.info("🔄 Step 1: Loading video...")
                progress_bar = st.progress(0)

                if video_source["type"] == "youtube":
                    video_path = video_processor.download_youtube_video(
                        video_source["url"], 
                        temp_dir
                    )
                else:
                    # Save uploaded file
                    video_path = os.path.join(temp_dir, "uploaded_video.mp4")
                    with open(video_path, "wb") as f:
                        f.write(video_source["file"].read())

                progress_bar.progress(20)
                st.success("✅ Video loaded successfully")

                # Step 2: Extract audio
                st.info("🔄 Step 2: Extracting audio...")
                audio_path = audio_utils.extract_audio(video_path, temp_dir)
                progress_bar.progress(40)
                st.success("✅ Audio extracted")

                # Step 3: Generate transcript
                st.info("🔄 Step 3: Generating transcript...")

                # Check if we can get YouTube transcript first
                transcript = None
                if video_source["type"] == "youtube":
                    try:
                        transcript = video_processor.get_youtube_transcript(video_source["url"])
                        st.info("✨ Using YouTube's official transcript for better accuracy!")
                    except:
                        st.info("📝 YouTube transcript not available, transcribing audio...")

                # Use audio transcription as fallback or if no YouTube transcript
                final_transcript = audio_utils.transcribe_audio(audio_path, transcript)
                progress_bar.progress(60)
                st.success("✅ Transcript generated")

                # Display transcript preview
                with st.expander("📝 Generated Transcript", expanded=False):
                    st.text_area("Transcript", final_transcript, height=150, disabled=True)

                # Step 4: Generate TTS audio
                st.info("🔄 Step 4: Generating TTS audio...")
                tts_audio_path = tts_generator.generate_speech(
                    final_transcript, 
                    temp_dir, 
                    voice=tts_voice,
                    speed=speech_speed
                )
                progress_bar.progress(80)
                st.success("✅ TTS audio generated")

                # Audio preview
                with st.expander("🔊 Preview Generated Audio", expanded=False):
                    if os.path.exists(tts_audio_path):
                        st.audio(tts_audio_path, format='audio/mp3')

                # Step 5: Replace audio in video
                st.info("🔄 Step 5: Replacing audio in video...")
                output_video_path = video_processor.replace_audio(
                    video_path, 
                    tts_audio_path, 
                    temp_dir
                )
                progress_bar.progress(100)
                st.success("✅ Video processing complete!")

                # Store result
                st.session_state.output_video_path = output_video_path
                st.session_state.processing_complete = True

    except Exception as e:
        st.error(f"❌ Processing failed: {str(e)}")
        st.error("Please check your inputs and try again.")

        # Show detailed error in expander for debugging
        with st.expander("🔍 Error Details", expanded=False):
            st.code(traceback.format_exc())

        cleanup_temp_files()

if __name__ == "__main__":
    main()