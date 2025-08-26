import streamlit as st
import os
import tempfile
import shutil
from pathlib import Path
import traceback

from video_processor import VideoProcessor
from basic_tts_generator import BasicTTSGenerator
from sync_first_tts import SyncFirstTTS

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

def main():
    st.title("🎬 Video SpeechSwap")
    st.markdown("""
    Replace video audio with AI-generated speech using **OpenAI Text-to-Speech**.
    Paste your text and choose from high-quality voices to replace the video's audio.
    """)
    
    # Sidebar for settings
    st.sidebar.header("Settings")
    
    # TTS Voice selection (OpenAI TTS voices)
    voice_options = {
        "alloy": "Alloy (Balanced, Versatile)",
        "echo": "Echo (Male, Clear)", 
        "fable": "Fable (Expressive, Warm)",
        "onyx": "Onyx (Male, Deep)",
        "nova": "Nova (Female, Bright)",
        "shimmer": "Shimmer (Female, Soft)"
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
    
    # Audio Synchronization Method
    sync_method = st.sidebar.selectbox(
        "Audio Sync Method",
        options=["sync_first", "pause_analysis", "smart", "stretch", "auto_speed", "loop", "fade", "shortest"],
        index=0,
        help="Choose synchronization method:\n"
             "• Sync-First: Calculate exact TTS speed upfront for perfect timing (RECOMMENDED)\n"
             "• Pause Analysis: Analyzes pauses in both audio files for precise timing\n"
             "• Smart: Advanced speech pattern analysis\n"
             "• Stretch: Simple time stretching\n"
             "• Auto Speed: Adjust TTS speed automatically\n"
             "• Loop/Fade/Shortest: Basic methods"
    )
    
    if sync_method == "sync_first":
        st.sidebar.success("🎯 Sync-First: Calculates exact TTS speed needed upfront. No post-processing = perfect quality!")
    elif sync_method == "pause_analysis":
        st.sidebar.info("🔍 Pause Analysis: Detects silence gaps in original and TTS audio, then stretches speech segments to match timing precisely.")
    elif sync_method == "smart":
        st.sidebar.info("🧠 Smart Sync: Advanced analysis using speech patterns and energy detection.")
    else:
        st.sidebar.info(f"📝 Using {sync_method} method for audio synchronization.")
    
    # Enhanced Stretch Options
    pause_detection = False
    if sync_method == "stretch":
        st.sidebar.markdown("---")
        pause_detection = st.sidebar.checkbox(
            "Add Pause Detection", 
            value=False,
            help="Preserve natural pause timing (slightly slower but better sync)"
        )
        if pause_detection:
            st.sidebar.info("🎯 Enhanced Stretch: Preserves natural pause timing for better sync")
        else:
            st.sidebar.info("⚡ Basic Stretch: Fast uniform time stretching")
    
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
        
        # Video thumbnail preview
        if uploaded_video is not None:
            st.markdown("---")
            st.subheader("📹 Video Thumbnail")
            
            try:
                # Save uploaded video temporarily
                temp_video_path = os.path.join(tempfile.gettempdir(), f"preview_{uploaded_video.name}")
                with open(temp_video_path, "wb") as f:
                    f.write(uploaded_video.getbuffer())
                
                # Generate thumbnail image using FFmpeg
                thumbnail_path = os.path.join(tempfile.gettempdir(), f"thumb_{uploaded_video.name}.jpg")
                import subprocess
                cmd = [
                    'ffmpeg', '-i', temp_video_path, '-ss', '00:00:01', '-vframes', '1', 
                    '-y', thumbnail_path
                ]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0 and os.path.exists(thumbnail_path):
                    # Display thumbnail image
                    st.image(thumbnail_path, caption=f"Frame from {uploaded_video.name}", width=400)
                else:
                    st.info("Could not generate video thumbnail")
                
                # Show video info
                file_size = len(uploaded_video.getbuffer()) / (1024 * 1024)  # Size in MB
                st.caption(f"📄 File: {uploaded_video.name}")
                st.caption(f"💾 Size: {file_size:.1f} MB")
                
                # Get video duration
                try:
                    cmd = ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration', '-of', 'csv=p=0', temp_video_path]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                    if result.returncode == 0 and result.stdout.strip():
                        duration = float(result.stdout.strip())
                        st.caption(f"⏱️ Duration: {duration:.1f} seconds")
                except Exception:
                    pass
                    
            except Exception as e:
                st.error(f"Could not process video: {str(e)}")
            
            st.markdown("---")
        
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
            # Estimate speech duration (average 150 words per minute)
            estimated_duration = (word_count / 150) * 60
            st.caption(f"📊 {word_count} words, {char_count} characters")
            st.caption(f"⏱️ Estimated speech duration: {estimated_duration:.1f} seconds")
    
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
                process_video_manual(uploaded_video, manual_text, tts_voice, speech_speed, sync_method, pause_detection)
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

def process_video_manual(uploaded_video, manual_text, tts_voice, speech_speed, sync_method, pause_detection=False):
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
            
            # Get video duration for auto-speed adjustment if needed
            video_info = video_processor.get_video_info(video_path)
            target_duration = video_info['duration'] if sync_method == "auto_speed" else None
            
            # Step 2: Generate TTS audio from manual text
            if sync_method == "sync_first":
                st.info("🔄 Step 2: Calculating optimal TTS speed and generating audio...")
                
                # Initialize sync-first TTS
                api_key = os.environ.get("OPENAI_API_KEY")
                if not api_key:
                    st.error("OpenAI API key not found. Please add your API key to environment variables.")
                    st.stop()
                
                sync_first_generator = SyncFirstTTS(api_key)
                
                # Get video duration
                video_duration = video_processor._get_duration(video_path)
                
                # Show speed calculation info
                speed_info = sync_first_generator.get_speed_info(manual_text, video_duration)
                
                with st.expander("📊 Speed Calculation Details", expanded=False):
                    st.write(f"**Text Analysis:**")
                    st.write(f"- Words: {speed_info['word_count']}")
                    st.write(f"- Natural duration: {speed_info['natural_duration']:.1f}s")
                    st.write(f"- Target duration: {speed_info['target_duration']:.1f}s")
                    st.write(f"- Required speed: {speed_info['required_speed']:.2f}x")
                    
                    if speed_info['is_feasible']:
                        st.success(f"✅ {speed_info['recommendation']}")
                    else:
                        st.warning(f"⚠️ {speed_info['recommendation']}")
                
                # Generate TTS at calculated speed
                try:
                    tts_audio_path, actual_speed = sync_first_generator.generate_sync_first_tts(
                        text=manual_text,
                        target_duration=video_duration,
                        voice=tts_voice,
                        output_path=os.path.join(temp_dir, "sync_first_audio.mp3")
                    )
                    progress_bar.progress(70)
                    st.success(f"✅ Sync-first TTS generated at {actual_speed:.2f}x speed!")
                except Exception as e:
                    st.error(f"❌ Sync-first TTS generation failed: {str(e)}")
                    st.stop()
            else:
                st.info("🔄 Step 2: Generating TTS audio...")
                if target_duration:
                    st.info(f"🎯 Target duration: {target_duration:.1f}s - Auto-adjusting speed...")
                
                tts_audio_path = tts_generator.generate_speech(
                    manual_text, 
                    temp_dir, 
                    voice=tts_voice,
                    speed=speech_speed,
                    target_duration=target_duration
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
            if sync_method == "sync_first":
                st.info("🔄 Step 3: Combining video with perfectly timed audio...")
                sync_status = st.empty()
                sync_status.info("🎯 No post-processing needed - audio already matches video duration!")
            elif sync_method == "stretch" and pause_detection:
                st.info("🔄 Step 3: Enhanced Stretch - preserving natural pause timing...")
                sync_status = st.empty()
                sync_status.info("🎯 Using pause-aware stretching for better synchronization")
            elif sync_method == "pause_analysis":
                st.info("🔄 Step 3: Pause Analysis - analyzing silence gaps in both audio files...")
                sync_status = st.empty()
                sync_status.info("🎯 Using pause analysis for precise timing synchronization")
            elif sync_method == "smart":
                st.info("🔄 Step 3: Smart synchronization - analyzing speech patterns...")
                sync_status = st.empty()
                sync_status.info("🧠 Using smart sync for better lip synchronization")
            else:
                st.info(f"🔄 Step 3: Combining video with new audio using '{sync_method}' method...")
                sync_status = st.empty()
            
            # Progress callback for sync methods
            sync_progress_bar = st.progress(70)
            def sync_progress_callback(p):
                sync_progress_bar.progress(70 + int(p * 0.3))
                if sync_method == "sync_first" and p < 100:
                    sync_status.info("🚀 Combining perfectly timed audio with video...")
                elif sync_method == "stretch" and pause_detection and p < 100:
                    if p < 50:
                        sync_status.info("🔊 Analyzing pause patterns...")
                    else:
                        sync_status.info("⚙️ Applying pause-aware stretching...")
                elif sync_method == "pause_analysis" and p < 100:
                    if p < 15:
                        sync_status.info("🔊 Extracting original audio...")
                    elif p < 40:
                        sync_status.info("📊 Analyzing pause structure in original audio...")
                    elif p < 65:
                        sync_status.info("🎤 Analyzing pause structure in TTS audio...")
                    elif p < 70:
                        sync_status.info("🔗 Creating pause-based timing mapping...")
                    else:
                        sync_status.info("⚙️ Applying pause-based timing adjustments...")
                elif sync_method == "smart" and p < 100:
                    if p < 25:
                        sync_status.info("🔊 Extracting original audio for analysis...")
                    elif p < 50:
                        sync_status.info("📊 Analyzing original speech patterns...")
                    elif p < 75:
                        sync_status.info("🎯 Mapping TTS audio to speech timing...")
                    else:
                        sync_status.info("⚙️ Applying timing adjustments...")
            
            output_video_path = video_processor.replace_audio(
                video_path, 
                tts_audio_path, 
                temp_dir,
                sync_method=sync_method,
                pause_detection=pause_detection,
                progress_callback=sync_progress_callback
            )
            sync_progress_bar.progress(100)
            
            if sync_method == "sync_first":
                sync_status.success("✅ Perfect sync achieved with no quality loss!")
            elif sync_method == "stretch" and pause_detection:
                sync_status.success("✅ Enhanced stretch complete - natural pause timing preserved!")
            elif sync_method == "pause_analysis":
                sync_status.success("✅ Pause analysis synchronization complete!")
            elif sync_method == "smart":
                sync_status.success("✅ Smart synchronization complete!")
            else:
                sync_status.success("✅ Audio synchronization complete!")
            
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