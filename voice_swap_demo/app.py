import os
import shutil
import tempfile
import traceback
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="SpeechSwap Voice Conversion", page_icon="🎙️", layout="wide")

# Disable HF Hub's Xet acceleration backend (hf-xet) before huggingface_hub is
# imported anywhere below. We only ever fetch two small ONNX files, so we don't
# need Xet's large-file chunked-transfer performance -- and hf-xet is a young,
# separately-versioned native (Rust) extension with reported platform-specific
# instability. Set as an env var, not a pip constraint, since huggingface_hub
# reads this to decide whether to even attempt loading the xet backend.
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")

try:
    from dotenv import load_dotenv

    from checkpoint_manager import download_and_verify, is_verified
    from elevenlabs_engine import ElevenLabsError, list_voices
    from pipeline import convert_video, ENGINE_ELEVENLABS, ENGINE_OPENVOICE, PipelineError, _sanitize_working_name
    from report import build_report, write_report
except Exception:
    # A catchable import-time failure (missing shared library, incompatible
    # native extension, etc.) would otherwise kill the process before Streamlit
    # ever renders anything, showing up only as a silent health-check failure
    # in the deploy log with no traceback. Surface it in the app itself instead.
    st.error("The app failed to start due to an import error:")
    st.code(traceback.format_exc())
    st.stop()

APP_DIR = Path(__file__).parent
ASSETS_DIR = APP_DIR / "assets"
OUTPUTS_DIR = APP_DIR / "outputs"

# Loads ELEVENLABS_API_KEY from a local .env file next to this script, if present.
# .env is gitignored -- this only ever reads from the user's own machine.
load_dotenv(APP_DIR / ".env")

# Set as a Streamlit Cloud secret (never in .env or committed) to run this as the
# public hosted demo: hides Custom Mode so anonymous visitors can't upload arbitrary
# video/audio to a shared, unmoderated server. Unset for the local desktop app,
# where Custom Mode is meant to be used. Also, deliberately no default ElevenLabs
# key is ever read here for hosted mode -- every visitor must bring their own.
HOSTED_DEMO = os.environ.get("SPEECHSWAP_HOSTED_DEMO") == "1"

# Bundled reference voices, generated via Piper (synthetic -- no real person's
# consent question for these specific bundled samples) and validated by measuring
# that openvoice's output pitch actually lands on each target, not just the source
# passing through: norman ~112Hz, john ~100Hz (deeper than norman), hfc_female
# ~237Hz, lessac (neutral -- included as a middle option distinct from the others).
VOICE_OPTIONS = {
    "john": ("John -- Deepest male", "demo_reference_john.wav"),
    "norman": ("Norman -- Deep male", "demo_reference_norman.wav"),
    "hfc_female": ("HFC Female -- Young / bright female", "demo_reference_hfc_female.wav"),
    "lessac": ("Lessac -- Neutral", "demo_reference_lessac.wav"),
}

for key, default in [
    ("demo_result", None), ("demo_report", None),
    ("custom_result", None), ("custom_report", None),
    ("custom_temp_dir", None),
    ("elevenlabs_voices", []),
]:
    if key not in st.session_state:
        st.session_state[key] = default


def _cleanup_custom_temp():
    if st.session_state.custom_temp_dir and os.path.exists(st.session_state.custom_temp_dir):
        shutil.rmtree(st.session_state.custom_temp_dir, ignore_errors=True)
        st.session_state.custom_temp_dir = None


def _run_pipeline_with_progress(video_path, reference_path, output_dir, output_filename, status, progress,
                                 engine=ENGINE_OPENVOICE, elevenlabs_api_key=None, elevenlabs_voice_id=None):
    status.text("Extracting original audio...")
    progress.progress(15)
    engine_label = "ElevenLabs (cloud, billed)" if engine == ENGINE_ELEVENLABS else "openvoice (local, CPU)"
    status.text(f"Running voice conversion ({engine_label})...")
    progress.progress(35)
    result = convert_video(
        video_path, reference_path, str(output_dir), output_filename=output_filename,
        engine=engine, elevenlabs_api_key=elevenlabs_api_key, elevenlabs_voice_id=elevenlabs_voice_id,
    )
    status.text("Validating output...")
    progress.progress(90)
    progress.progress(100)
    status.text("Done.")
    return result


def render_limitations_notice():
    st.info(
        "**v1 limitations, by design**: works best on short clips with one clearly "
        "audible speaker and little to no background music. Multiple speakers will "
        "all be converted to the same target voice (no speaker separation). "
        "Background music/noise may produce artifacts. CPU-only -- no GPU required."
    )


def render_run_demo_tab():
    st.markdown("### Bundled demo")
    st.write(
        "Runs the real pipeline on a bundled sample video and a synthetic "
        "(rights-clean) reference voice of your choice -- not a canned result."
    )

    demo_voice_key = st.selectbox(
        "Voice", options=list(VOICE_OPTIONS.keys()),
        format_func=lambda k: VOICE_OPTIONS[k][0], key="demo_voice_select",
    )
    demo_voice_file = VOICE_OPTIONS[demo_voice_key][1]

    demo_col1, demo_col2 = st.columns(2)
    with demo_col1:
        st.markdown("**Original**")
        if (ASSETS_DIR / "demo_video.mp4").exists():
            st.video(str(ASSETS_DIR / "demo_video.mp4"))
    with demo_col2:
        st.markdown("**Reference voice**")
        if (ASSETS_DIR / demo_voice_file).exists():
            st.audio(str(ASSETS_DIR / demo_voice_file))

    if st.button("▶️ Run Demo", type="primary"):
        progress = st.progress(0)
        status = st.empty()
        try:
            output_filename = f"demo_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.mp4"
            result = _run_pipeline_with_progress(
                str(ASSETS_DIR / "demo_video.mp4"),
                str(ASSETS_DIR / demo_voice_file),
                OUTPUTS_DIR, output_filename, status, progress,
            )
            report = build_report(result)
            write_report(report, str(OUTPUTS_DIR), filename=f"{Path(output_filename).stem}_report.json")
            st.session_state.demo_result = result
            st.session_state.demo_report = report
            st.success("Demo run complete.")
        except (PipelineError, Exception) as e:
            st.error(f"Demo run failed: {e}")
            print(traceback.format_exc())

    if st.session_state.demo_result:
        result = st.session_state.demo_result
        report = st.session_state.demo_report
        st.markdown("### Result")
        result_col1, result_col2 = st.columns(2)
        with result_col1:
            st.markdown("**Original**")
            st.video(str(ASSETS_DIR / "demo_video.mp4"))
        with result_col2:
            st.markdown("**Voice-converted**")
            st.video(result.output_video_path)

        if report["validation_status"] != "pass":
            st.warning(f"Validation warnings: {report['warnings']}")
        else:
            st.success(
                f"Validated: {report['video_frames_out']}/{report['video_frames_in']} frames "
                f"preserved, streams aligned, ran in {report['total_runtime_seconds']}s."
            )
        st.caption(f"Saved to: {result.output_video_path}")

        with open(result.output_video_path, "rb") as f:
            st.download_button("📥 Download this result", f.read(),
                                file_name=os.path.basename(result.output_video_path),
                                mime="video/mp4")

    st.markdown("---")
    with st.expander("📼 Pre-rendered example (not live -- generated ahead of time)"):
        st.caption(
            "This is a pre-generated example using the same pipeline, shown here "
            "as a reference in case you haven't run the live demo yet. It is not "
            "the result of a fresh run."
        )
        if (ASSETS_DIR / "prerendered_example.mp4").exists():
            st.video(str(ASSETS_DIR / "prerendered_example.mp4"))


def render_custom_mode_tab():
    st.markdown("### Your video, your choice of voice")

    uploaded_video = st.file_uploader("Video file", type=["mp4", "mov", "mkv", "webm", "avi"])

    voice_source = st.radio(
        "Reference voice",
        options=["Use a bundled voice", "Upload my own reference voice", "ElevenLabs (paid, your API key)"],
        horizontal=True,
    )

    uploaded_reference = None
    custom_voice_key = None
    engine = ENGINE_OPENVOICE
    elevenlabs_api_key = None
    elevenlabs_voice_id = None

    if voice_source == "Use a bundled voice":
        custom_voice_key = st.selectbox(
            "Voice", options=list(VOICE_OPTIONS.keys()),
            format_func=lambda k: VOICE_OPTIONS[k][0], key="custom_voice_select",
        )
        if (ASSETS_DIR / VOICE_OPTIONS[custom_voice_key][1]).exists():
            st.audio(str(ASSETS_DIR / VOICE_OPTIONS[custom_voice_key][1]))
    elif voice_source == "Upload my own reference voice":
        uploaded_reference = st.file_uploader("Reference voice sample (WAV, 5-30s)", type=["wav"])
        st.caption(
            "Only upload a voice you own or have explicit permission to use -- "
            "see the consent confirmation below."
        )
    else:
        engine = ENGINE_ELEVENLABS
        st.caption(
            "Uses your own ElevenLabs account and voice library. This makes a real, "
            "billed API call (roughly $0.12 per minute of source audio, at ElevenLabs' "
            "current published rate) -- nothing free about this path."
        )
        elevenlabs_api_key = st.text_input(
            "ElevenLabs API key", type="password", key="elevenlabs_api_key_input",
            value=os.environ.get("ELEVENLABS_API_KEY", ""),
            help="Loaded from .env if present, or paste your own -- kept in memory for this "
                 "session only, never written to disk or included in the report.",
        )
        if elevenlabs_api_key:
            if st.button("Load my ElevenLabs voices"):
                try:
                    st.session_state.elevenlabs_voices = list_voices(elevenlabs_api_key)
                    if not st.session_state.elevenlabs_voices:
                        st.warning("No voices found on this account.")
                except ElevenLabsError as e:
                    st.error(str(e))
                    st.session_state.elevenlabs_voices = []
            if st.session_state.elevenlabs_voices:
                voice_names = {v["voice_id"]: v["name"] for v in st.session_state.elevenlabs_voices}
                elevenlabs_voice_id = st.selectbox(
                    "ElevenLabs voice", options=list(voice_names.keys()),
                    format_func=lambda vid: voice_names[vid], key="elevenlabs_voice_select",
                )
        else:
            st.caption('Enter your API key, then click "Load my ElevenLabs voices".')

    consent = st.checkbox(
        "I confirm that I own this voice recording, or have explicit permission "
        "from the speaker, to use it for voice conversion."
    )
    if not consent:
        st.caption("This checkbox must be checked before conversion can run.")

    has_reference = (
        custom_voice_key is not None
        or uploaded_reference is not None
        or (engine == ENGINE_ELEVENLABS and elevenlabs_voice_id is not None)
    )
    can_convert = uploaded_video is not None and has_reference and consent
    if st.button("🎬 Convert", type="primary", disabled=not can_convert):
        _cleanup_custom_temp()
        temp_dir = tempfile.mkdtemp(prefix="voiceswap_custom_")
        st.session_state.custom_temp_dir = temp_dir

        video_path = os.path.join(temp_dir, _sanitize_working_name(uploaded_video.name))
        with open(video_path, "wb") as f:
            f.write(uploaded_video.getbuffer())

        if custom_voice_key is not None:
            reference_path = str(ASSETS_DIR / VOICE_OPTIONS[custom_voice_key][1])
        elif uploaded_reference is not None:
            reference_path = os.path.join(temp_dir, _sanitize_working_name(uploaded_reference.name))
            with open(reference_path, "wb") as f:
                f.write(uploaded_reference.getbuffer())
        else:
            reference_path = None  # ElevenLabs: target voice comes from the account, not a clip

        progress = st.progress(0)
        status = st.empty()
        try:
            output_filename = f"custom_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.mp4"
            result = _run_pipeline_with_progress(
                video_path, reference_path, OUTPUTS_DIR, output_filename, status, progress,
                engine=engine, elevenlabs_api_key=elevenlabs_api_key, elevenlabs_voice_id=elevenlabs_voice_id,
            )
            consent_record = {
                "confirmed": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            report = build_report(result, consent=consent_record)
            write_report(report, str(OUTPUTS_DIR), filename=f"{Path(output_filename).stem}_report.json")
            st.session_state.custom_result = result
            st.session_state.custom_report = report
            st.success("Conversion complete.")
        except (PipelineError, Exception) as e:
            st.error(f"Conversion failed: {e}")
            print(traceback.format_exc())

    if st.session_state.custom_result:
        result = st.session_state.custom_result
        report = st.session_state.custom_report
        st.markdown("### Result")
        st.video(result.output_video_path)
        if report["validation_status"] != "pass":
            st.warning(f"Validation warnings: {report['warnings']}")
        else:
            st.success(
                f"Validated: {report['video_frames_out']}/{report['video_frames_in']} frames "
                f"preserved, streams aligned."
            )
        st.caption(f"Saved to: {result.output_video_path}")
        with open(result.output_video_path, "rb") as f:
            st.download_button("📥 Download result", f.read(),
                                file_name=os.path.basename(result.output_video_path),
                                mime="video/mp4")


def _ensure_checkpoint():
    """setup.bat downloads the voice model ahead of time for the local desktop app.
    There's no equivalent setup step on Streamlit Cloud, so do it here instead, once,
    on cold start -- this is a no-op after the first successful run since is_verified()
    short-circuits without any network call.
    """
    if is_verified():
        return
    with st.spinner("Setting up the voice-conversion model (one-time, ~130MB)..."):
        status = st.empty()
        download_and_verify(progress_callback=status.text)
        status.empty()


def main():
    _ensure_checkpoint()

    st.title("🎙️ SpeechSwap Voice Conversion")
    st.caption(
        "Converts a video's voice to a different one while keeping the original "
        "video and its exact timing untouched -- no re-synthesis, no lip-sync "
        "regeneration needed."
    )
    render_limitations_notice()

    tab_demo, tab_custom = st.tabs(["▶️ Run Demo", "📤 Custom Mode"])

    with tab_demo:
        render_run_demo_tab()

    with tab_custom:
        if HOSTED_DEMO:
            st.info(
                "Custom Mode -- upload your own video, use your own reference voice, "
                "or use ElevenLabs -- is available in the downloadable local app, not "
                "this public demo, so anonymous visitors can't upload arbitrary "
                "video/audio to a shared, unmoderated server. See the "
                "[repository](https://github.com/TeachingTheMachine/SpeechSwap/tree/main/voice_swap_demo) "
                "for setup instructions to run it yourself."
            )
        else:
            render_custom_mode_tab()


if __name__ == "__main__":
    main()
