import streamlit as st
import os
import tempfile
import shutil
from pathlib import Path
import traceback

from video_processor import VideoProcessor
from basic_tts_generator import BasicTTSGenerator

# Configure page
st.set_page_config(
    page_title="YouTube Voice Replacement - Simple Version",
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

def cleanup_temp_files():
    """Clean up temporary files"""
    if st.session_state.temp_dir and os.path.exists(st.session_state.temp_dir):
        shutil.rmtree(st.session_state.temp_dir, ignore_errors=True)
        st.session_state.temp_dir = None

def main():
    st.title("🎬 YouTube Voice Replacement - Simple Version")
    st.markdown("""
    Replace video audio with AI-generated speech using **gTTS (Google Text-to-Speech)**.
    No authentication required - completely free to use!
    """)
    
    # Sidebar for settings
    st.sidebar.header("Settings")
    
    # TTS Voice selection (Google Cloud TTS voices)
    voice_options = {
        "en-US-Wavenet-D": "English US (Male, Natural)",
        "en-US-Wavenet-F": "English US (Female, Natural)", 
        "en-GB-Wavenet-A": "English UK (Female, Natural)",
        "en-GB-Wavenet-B": "English UK (Male, Natural)",
        "en-AU-Wavenet-A": "English Australia (Female, Natural)",
        "en-AU-Wavenet-B": "English Australia (Male, Natural)",
        "en-CA-Wavenet-A": "English Canada (Female, Natural)",
        "en-CA-Wavenet-B": "English Canada (Male, Natural)"
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
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("Input")
        
        # Input method selection - simplified to just manual text + video
        st.subheader("Manual Text Input Method")
        st.info("📝 Upload a video file and paste the text you want as the new audio")
        
        uploaded_video = st.file_uploader(
            "Upload video file:",
            type=['mp4', 'avi', 'mov', 'mkv', 'webm'],
            help="Upload the video file that you want to replace audio for"
        )
        
        manual_text = st.text_area(
            "Enter the text you want to convert to speech:",
            height=200,
            placeholder="Paste or type the text that should replace the video's audio...",
            help="This text will be converted to speech and replace the video's audio"
        )
        
        # Show text statistics
        if manual_text:
            word_count = len(manual_text.split())
            char_count = len(manual_text)
            st.caption(f"📊 {word_count} words, {char_count} characters")
    
    with col2:
        st.header("Process")
        
        # Show what's needed
        if not uploaded_video:
            st.warning("⚠️ Please upload a video file first")
        elif not manual_text:
            st.warning("⚠️ Please enter text to convert to speech")
        else:
            st.success("✅ Ready to process!")
        
        # Show button state clearly
        if uploaded_video and manual_text:
            if st.button("🚀 Start Processing", type="primary", use_container_width=True):
                process_video_manual(uploaded_video, manual_text, tts_voice, speech_speed)
        else:
            st.button("🚀 Start Processing", type="primary", use_container_width=True, disabled=True, help="Upload video and enter text first")
        
        if st.session_state.processing_complete and st.session_state.output_video_path:
            st.success("✅ Processing Complete!")
            
            # Download button
            if os.path.exists(st.session_state.output_video_path):
                with open(st.session_state.output_video_path, "rb") as file:
                    st.download_button(
                        "📥 Download Processed Video",
                        data=file.read(),
                        file_name="processed_video.mp4",
                        mime="video/mp4",
                        use_container_width=True
                    )
        
        # Reset button
        if st.button("🔄 Reset", use_container_width=True):
            cleanup_temp_files()
            st.session_state.processing_complete = False
            st.session_state.output_video_path = None
            st.rerun()

def process_video_manual(uploaded_video, manual_text, tts_voice, speech_speed):
    """Process video with manual text input"""
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    st.session_state.temp_dir = temp_dir
    
    # Progress tracking
    progress_container = st.container()
    
    try:
        # Initialize processors
        video_processor = VideoProcessor()
        tts_generator = BasicTTSGenerator()
        
        with progress_container:
            # Step 1: Save uploaded video
            st.info("🔄 Step 1: Processing uploaded video...")
            progress_bar = st.progress(0)
            
            video_path = os.path.join(temp_dir, "uploaded_video.mp4")
            with open(video_path, "wb") as f:
                f.write(uploaded_video.read())
            
            progress_bar.progress(25)
            st.success("✅ Video saved successfully")
            
            # Step 2: Generate TTS audio from manual text
            st.info("🔄 Step 2: Generating TTS audio...")
            tts_audio_path = tts_generator.generate_speech(
                manual_text, 
                temp_dir, 
                voice=tts_voice,
                speed=speech_speed
            )
            progress_bar.progress(70)
            st.success("✅ TTS audio generated")
            
            # Show text preview
            with st.expander("📝 Text Used for TTS", expanded=False):
                st.text_area("Generated speech from:", manual_text, height=100, disabled=True)
            
            # Audio preview
            with st.expander("🔊 Preview Generated Audio", expanded=False):
                if os.path.exists(tts_audio_path):
                    st.audio(tts_audio_path, format='audio/mp3')
            
            # Step 3: Replace audio in video
            st.info("🔄 Step 3: Combining video with new audio...")
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