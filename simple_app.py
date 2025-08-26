import streamlit as st
import os
import tempfile
import shutil
import subprocess
from pathlib import Path
import traceback

from video_processor import VideoProcessor
from basic_tts_generator import BasicTTSGenerator

# Configure page
st.set_page_config(
    page_title="Video SpeechSwap",
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

def process_video(uploaded_video, manual_text, tts_voice, speech_speed, pause_detection):
    """Process video with stretch synchronization method"""
    try:
        st.session_state.processing_complete = False
        
        # Create temp directory
        if st.session_state.temp_dir:
            cleanup_temp_files()
        st.session_state.temp_dir = tempfile.mkdtemp(prefix="speechswap_")
        
        # Save uploaded video
        video_path = os.path.join(st.session_state.temp_dir, uploaded_video.name)
        with open(video_path, "wb") as f:
            f.write(uploaded_video.getbuffer())
        
        progress_container = st.container()
        with progress_container:
            progress_bar = st.progress(0)
            status_text = st.empty()
        
        # Initialize processors
        video_processor = VideoProcessor()
        tts_generator = BasicTTSGenerator()
        
        # Extract audio from video
        status_text.text("Extracting audio from video...")
        progress_bar.progress(20)
        
        audio_path = os.path.join(st.session_state.temp_dir, "extracted_audio.wav")
        video_processor.extract_audio(video_path, audio_path)
        
        # Generate TTS audio
        status_text.text("Generating AI speech...")
        progress_bar.progress(40)
        
        tts_audio_path = os.path.join(st.session_state.temp_dir, "tts_audio.mp3")
        tts_generator.generate_tts(manual_text, tts_audio_path, voice=tts_voice, speed=speech_speed)
        
        # Synchronize audio using stretch method
        status_text.text("Synchronizing audio with video...")
        progress_bar.progress(70)
        
        output_video_path = video_processor.replace_audio(
            video_path, 
            tts_audio_path, 
            st.session_state.temp_dir, 
            sync_method="stretch",
            pause_detection=pause_detection
        )
        
        progress_bar.progress(100)
        status_text.text("Processing complete!")
        
        st.session_state.output_video_path = output_video_path
        st.session_state.processing_complete = True
        
        st.success("Video processing completed successfully!")
        st.rerun()
        
    except Exception as e:
        st.error(f"Processing failed: {str(e)}")
        if st.session_state.temp_dir:
            cleanup_temp_files()
        print(f"Error details: {traceback.format_exc()}")

def main():
    # Header Section
    st.markdown("""
    # 🎬 Video SpeechSwap
    **Professional AI voice replacement for your videos**
    
    Transform any video with high-quality AI-generated speech using OpenAI's advanced text-to-speech technology.
    """)
    
    st.markdown("---")
    
    # Main Content Layout
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # Video Upload Section
        st.markdown("### 📤 Upload Video")
        uploaded_video = st.file_uploader(
            "Choose a video file",
            type=['mp4', 'avi', 'mov', 'mkv', 'webm'],
            help="Select the video file you want to process"
        )
        
        # Video Preview
        if uploaded_video is not None:
            st.markdown("#### Preview")
            try:
                temp_video_path = os.path.join(tempfile.gettempdir(), f"preview_{uploaded_video.name}")
                with open(temp_video_path, "wb") as f:
                    f.write(uploaded_video.getbuffer())
                
                thumbnail_path = os.path.join(tempfile.gettempdir(), f"thumb_{uploaded_video.name}.jpg")
                cmd = ['ffmpeg', '-i', temp_video_path, '-ss', '00:00:01', '-vframes', '1', '-y', thumbnail_path]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0 and os.path.exists(thumbnail_path):
                    st.image(thumbnail_path, width=400)
                
                # Video info
                file_size = len(uploaded_video.getbuffer()) / (1024 * 1024)
                try:
                    cmd = ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration', '-of', 'csv=p=0', temp_video_path]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                    duration = float(result.stdout.strip()) if result.returncode == 0 else 0
                    st.caption(f"📁 {uploaded_video.name} • {file_size:.1f}MB • {duration:.1f}s")
                except:
                    st.caption(f"📁 {uploaded_video.name} • {file_size:.1f}MB")
                    
            except Exception:
                st.success(f"✅ {uploaded_video.name} uploaded successfully")
        
        st.markdown("---")
        
        # Text Input Section
        st.markdown("### ✍️ Script Text")
        manual_text = st.text_area(
            "Enter your script",
            height=200,
            placeholder="Type or paste the text that will become the new audio for your video...",
            help="This text will be converted to speech and replace the original audio"
        )
        
        # Text Statistics
        if manual_text:
            word_count = len(manual_text.split())
            char_count = len(manual_text)
            estimated_duration = (word_count / 150) * 60
            
            col_stat1, col_stat2, col_stat3 = st.columns(3)
            with col_stat1:
                st.metric("Words", word_count)
            with col_stat2:
                st.metric("Characters", char_count)  
            with col_stat3:
                st.metric("Est. Duration", f"{estimated_duration:.1f}s")
    
    with col2:
        # Settings Panel
        st.markdown("### ⚙️ Voice Settings")
        
        # Voice Selection
        voice_options = {
            "alloy": "Alloy - Balanced & versatile",
            "echo": "Echo - Clear & professional", 
            "fable": "Fable - Warm & expressive",
            "onyx": "Onyx - Deep & authoritative",
            "nova": "Nova - Bright & energetic",
            "shimmer": "Shimmer - Soft & gentle"
        }
        
        tts_voice = st.selectbox(
            "AI Voice",
            options=list(voice_options.keys()),
            format_func=lambda x: voice_options[x],
            help="Choose the AI voice personality"
        )
        
        # Speed Control
        speech_speed = st.slider(
            "Speech Speed",
            min_value=0.5,
            max_value=2.0,
            value=1.0,
            step=0.1,
            help="Adjust playback speed (1.0 = normal)"
        )
        
        st.markdown("---")
        
        # Synchronization Options
        st.markdown("### 🎯 Audio Sync")
        st.info("**Stretch Method**: Adjusts audio timing to match video duration perfectly")
        
        pause_detection = st.checkbox(
            "Enhanced pause detection",
            value=True,
            help="Preserves natural speech pauses for better synchronization"
        )
        
        st.markdown("---")
        
        # Processing Section
        st.markdown("### 🚀 Generate")
        
        # Status indicators
        if not uploaded_video:
            st.warning("Upload a video file")
        elif not manual_text:
            st.warning("Enter script text")
        else:
            st.success("Ready to process")
        
        # Process button
        if uploaded_video and manual_text:
            if st.button("🎬 Create Video", type="primary", use_container_width=True):
                process_video(uploaded_video, manual_text, tts_voice, speech_speed, pause_detection)
        else:
            st.button("🎬 Create Video", disabled=True, use_container_width=True)
    
    # Results Section
    if st.session_state.processing_complete and st.session_state.output_video_path:
        st.markdown("---")
        st.markdown("### 🎉 Results")
        
        if os.path.exists(st.session_state.output_video_path):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.success("Your video is ready!")
                with open(st.session_state.output_video_path, "rb") as file:
                    st.download_button(
                        "📥 Download Video",
                        data=file.read(),
                        file_name="speechswap_output.mp4",
                        mime="video/mp4",
                        use_container_width=True
                    )
            
            with col2:
                if st.button("🔄 Process Another Video", use_container_width=True):
                    cleanup_temp_files()
                    st.session_state.processing_complete = False
                    st.session_state.output_video_path = None
                    st.rerun()

if __name__ == "__main__":
    main()