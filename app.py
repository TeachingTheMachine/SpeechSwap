"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                   app.py                                    ║
║                                                                              ║
║  Author: Vanessa Crosby                                                      ║
║  Date Created: August 23, 2025                                              ║
║  File Purpose: Main Streamlit app with OAuth YouTube authentication         ║
║  Date Modified: August 23, 2025 5:15 PM                                     ║
║  Mod Purpose: Added OAuth authentication flow for YouTube Data API          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import os
import tempfile
import shutil
from pathlib import Path
import traceback

from video_processor import VideoProcessor
from audio_utils import AudioUtils
from simple_tts_generator import SimpleTTSGenerator

st.set_page_config(page_title="YouTube Voice Replacement", page_icon="🎬", layout="wide")

if 'processing_complete' not in st.session_state:
    st.session_state.processing_complete = False
if 'output_video_path' not in st.session_state:
    st.session_state.output_video_path = None
if 'temp_dir' not in st.session_state:
    st.session_state.temp_dir = None
if 'transcript_only_mode' not in st.session_state:
    st.session_state.transcript_only_mode = False
if 'oauth_authenticated' not in st.session_state:
    st.session_state.oauth_authenticated = False
if 'video_processor' not in st.session_state:
    st.session_state.video_processor = VideoProcessor()

def cleanup_temp_files():
    if st.session_state.temp_dir and os.path.exists(st.session_state.temp_dir):
        shutil.rmtree(st.session_state.temp_dir, ignore_errors=True)
        st.session_state.temp_dir = None

def main():
    st.title("🎬 YouTube Voice Replacement")
    st.markdown("""
    Replace YouTube video audio with clear AI-generated speech using **Google Cloud TTS**.

    💡 **Length Control**: Modify `MAX_WORDS` in `tts_generator.py` to control output length.
    """)

    creds_available = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS_JSON') is not None
    youtube_api_available = os.environ.get('YOUTUBE_API_KEY') is not None
    oauth_available = os.environ.get('GOOGLE_OAUTH_CREDENTIALS_JSON') is not None

    col1_status, col2_status, col3_status = st.columns(3)
    with col1_status:
        if creds_available:
            st.success("✅ Google Cloud TTS")
        else:
            st.error("❌ Google Cloud TTS")

    with col2_status:
        if youtube_api_available:
            st.success("✅ YouTube API Key")
        else:
            st.error("❌ YouTube API Key")

    with col3_status:
        if oauth_available:
            st.success("✅ OAuth Credentials")
        else:
            st.error("❌ OAuth Credentials")

    if not creds_available:
        st.info("Add GOOGLE_APPLICATION_CREDENTIALS_JSON to Replit Secrets")

    if not youtube_api_available:
        st.info("Add YOUTUBE_API_KEY to Replit Secrets for API access")

    if not oauth_available:
        st.info("Add GOOGLE_OAUTH_CREDENTIALS_JSON to Replit Secrets for OAuth")

    try:
        from tts_generator import MAX_WORDS
        if MAX_WORDS and MAX_WORDS > 0:
            st.warning(f"🧪 **Current Setting**: Limited to {MAX_WORDS} words. Change `MAX_WORDS` in `tts_generator.py` for full transcript.")
        else:
            st.info("📜 **Current Setting**: Full transcript mode (no word limit)")
    except:
        st.info("📜 **Length Setting**: Check `tts_generator.py` for current limit")

    st.sidebar.header("🎙️ Voice Settings")

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
        index=0
    )

    speech_speed = st.sidebar.slider("Speech Speed", min_value=0.5, max_value=2.0, value=1.0, step=0.1)

    st.sidebar.header("⚙️ Transcript Method")

    transcript_methods = []
    if oauth_available:
        transcript_methods.append("OAuth YouTube API (Most Legal)")
    if youtube_api_available:
        transcript_methods.append("YouTube API Key (Limited)")
    transcript_methods.extend([
        "YouTube Transcript Scraper (May be blocked)",
        "Manual Text Input"
    ])

    transcript_method = st.sidebar.radio("Choose transcript method:", transcript_methods)

    if transcript_method == "OAuth YouTube API (Most Legal)":
        st.sidebar.success("🏛️ Using OAuth - fully legal and reliable")

        if not st.session_state.oauth_authenticated:
            st.sidebar.warning("🔑 OAuth authentication required")

            if st.sidebar.button("🚀 Authenticate with Google"):
                try:
                    auth_url, flow = st.session_state.video_processor.get_oauth_url()
                    st.session_state.oauth_flow = flow

                    st.sidebar.markdown(f"**Step 1:** [Click here to authenticate]({auth_url})")
                    st.sidebar.info("After clicking the link above, you'll get an authorization code. Copy and paste it below.")

                except Exception as e:
                    st.sidebar.error(f"OAuth setup failed: {str(e)}")

            if 'oauth_flow' in st.session_state:
                auth_code = st.sidebar.text_input("Enter authorization code:")
                if st.sidebar.button("Complete Authentication"):
                    try:
                        st.session_state.video_processor.complete_oauth_flow(st.session_state.oauth_flow, auth_code)
                        st.session_state.oauth_authenticated = True
                        st.sidebar.success("✅ OAuth authentication successful!")
                        st.rerun()
                    except Exception as e:
                        st.sidebar.error(f"Authentication failed: {str(e)}")
        else:
            st.sidebar.success("✅ OAuth authenticated")

    elif transcript_method == "YouTube API Key (Limited)":
        st.sidebar.warning("⚠️ API key method - limited functionality")
    elif transcript_method == "YouTube Transcript Scraper (May be blocked)":
        st.sidebar.warning("⚠️ May be blocked by YouTube's anti-bot protection")
    else:
        st.sidebar.info("📝 Paste your own text to convert to speech")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.header("📥 Input")

        video_source = None

        if transcript_method == "Manual Text Input":
            manual_text = st.text_area("Enter text to convert to speech:", height=200, placeholder="Paste your text here...")
            if manual_text:
                video_source = {"type": "manual", "text": manual_text, "method": transcript_method}
        else:
            youtube_url = st.text_input("Enter YouTube URL:", placeholder="https://www.youtube.com/watch?v=...")
            if youtube_url:
                video_source = {"type": "youtube", "url": youtube_url, "method": transcript_method}

    with col2:
        st.header("🚀 Process")

        can_process = False
        if video_source:
            if transcript_method == "OAuth YouTube API (Most Legal)" and not st.session_state.oauth_authenticated:
                st.info("🔑 Complete OAuth authentication first")
            else:
                can_process = True

        if can_process:
            if st.button("🎬 Start Processing", type="primary", use_container_width=True):
                process_video(video_source, tts_voice, speech_speed)
        else:
            st.info("👆 Enter input and complete authentication")

        if st.session_state.processing_complete and st.session_state.output_video_path:
            st.success("✅ Processing Complete!")

            if os.path.exists(st.session_state.output_video_path):
                with open(st.session_state.output_video_path, "rb") as file:
                    st.download_button("🎵 Download Generated Audio", data=file.read(), file_name="generated_audio.mp3", mime="audio/mp3", use_container_width=True)

        if st.button("🔄 Reset", use_container_width=True):
            cleanup_temp_files()
            st.session_state.processing_complete = False
            st.session_state.output_video_path = None
            st.session_state.transcript_only_mode = False
            st.session_state.oauth_authenticated = False
            st.session_state.video_processor = VideoProcessor()
            st.rerun()

def process_video(video_source, tts_voice, speech_speed):
    temp_dir = tempfile.mkdtemp()
    st.session_state.temp_dir = temp_dir
    st.session_state.transcript_only_mode = True

    try:
        video_processor = st.session_state.video_processor
        audio_utils = AudioUtils()

        try:
            tts_generator = TTSGenerator()
        except Exception as e:
            st.error(f"❌ Failed to initialize Google Cloud TTS: {str(e)}")
            return

        st.markdown("### 🔄 Processing Steps")

        if video_source["type"] == "manual":
            transcript = video_source["text"]
            st.success("✅ Using manual text input")
        else:
            with st.status("Step 1: Extracting transcript...", expanded=True) as status:
                try:
                    if video_source["method"] == "OAuth YouTube API (Most Legal)":
                        st.info("🏛️ Using YouTube OAuth API (Fully Legal)")
                        video_source["url"] = "https://www.youtube.com/watch?v=HloC4xMg4Z4"
                        transcript = video_processor.get_youtube_transcript_oauth(video_source["url"])
                        
                    elif video_source["method"] == "YouTube API Key (Limited)":
                        st.info("🔑 Using YouTube API Key")
                        transcript = video_processor.get_youtube_transcript_official_api(video_source["url"])
                    else:
                        st.info("🔍 Using transcript scraper")
                        transcript = video_processor.get_youtube_transcript(video_source["url"])

                    status.update(label="✅ Step 1: Transcript extracted successfully!", state="complete")
                except Exception as e:
                    status.update(label="❌ Step 1: Failed to extract transcript", state="error")
                    raise e

        with st.expander("📝 Extracted Text", expanded=True):
            st.text_area("Text Content", transcript, height=150, disabled=True)

            word_count = len(transcript.split())
            char_count = len(transcript)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📊 Characters", f"{char_count:,}")
            with col2:
                st.metric("📝 Words", f"{word_count:,}")
            with col3:
                estimated_cost = (char_count / 1000000) * 16
                st.metric("💰 Full Cost", f"${estimated_cost:.4f}")

        with st.status("Step 2: Generating TTS audio with Google Cloud...", expanded=True) as status:
            try:
                st.info(f"🎙️ Using voice: **{voice_options[tts_voice]}**")
                st.info(f"⚡ Speed: **{speech_speed}x**")

                tts_audio_path = tts_generator.generate_speech(transcript, temp_dir, voice=tts_voice, speed=speech_speed)
                status.update(label="✅ Step 2: Google Cloud TTS generation complete!", state="complete")
            except Exception as e:
                status.update(label="❌ Step 2: Failed to generate audio", state="error")
                raise e

        st.session_state.output_video_path = tts_audio_path
        st.session_state.processing_complete = True

        with st.expander("🔊 Preview Generated Audio", expanded=True):
            if os.path.exists(tts_audio_path):
                st.audio(tts_audio_path, format='audio/mp3')

                try:
                    file_size = os.path.getsize(tts_audio_path) / 1024 / 1024
                    st.metric("💾 File Size", f"{file_size:.2f} MB")
                except:
                    st.info("File statistics unavailable")

        st.success("🎉 **Processing Complete!** Your audio is ready for download!")

    except Exception as e:
        st.error(f"❌ **Processing failed:** {str(e)}")

        with st.expander("🔍 Error Details", expanded=False):
            st.code(traceback.format_exc())

        cleanup_temp_files()

if __name__ == "__main__":
    main()