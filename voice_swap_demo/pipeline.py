"""The validated voice-conversion pipeline: extract -> convert -> pad -> mux -> validate.

Every ffmpeg flag and ordering choice here was found necessary by hands-on testing
against a real source video during this project's validation spike, not assumed:

- No `-avoid_negative_ts make_zero`: confirmed this actively caused a ~21ms stream
  misalignment on a clean source file (it's meant to fix negative timestamps, and
  forcing it on a source that doesn't have any just introduces a shift).
- Audio is padded to the video's exact duration rather than using `-shortest` to trim
  the video down to the (slightly shorter) converted audio: on a source with B-frame
  reordering, `-c:v copy` can only trim at GOP boundaries, not frame-exactly, so
  `-shortest` over-trimmed by 3 frames on a 10s/24fps test clip. Padding audio instead
  means the video is never touched at all.
"""

import os
import secrets
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

import soundfile as sf
from voiceclonnx import VoiceCloner

from elevenlabs_engine import ElevenLabsError, speech_to_speech

ENGINE_OPENVOICE = "openvoice"
ENGINE_ELEVENLABS = "elevenlabs"
ENGINE = ENGINE_OPENVOICE  # default, kept for backward compatibility


class PipelineError(Exception):
    pass


@dataclass
class PipelineResult:
    output_video_path: str
    source_duration: float
    reference_duration: float
    converted_duration_raw: float
    final_duration: float
    conversion_runtime_seconds: float
    total_runtime_seconds: float
    engine: str
    output_sample_rate: int
    video_frames_in: int
    video_frames_out: int
    stream_start_times_match: bool
    warnings: list = field(default_factory=list)


def _run_ffmpeg(args, description):
    cmd = ["ffmpeg", "-y", *args]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise PipelineError(f"{description} failed: {result.stderr[-2000:]}")


def _ffprobe_value(path, stream_select, entry):
    """stream_select: a stream specifier like 'v:0'/'a:0' for -show_entries stream=...,
    or the literal 'format' for -show_entries format=... (container-level, e.g. overall
    duration) -- -select_streams doesn't apply to format-level queries.
    """
    if stream_select == "format":
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", f"format={entry}", "-of", "default=noprint_wrappers=1:nokey=1",
            path,
        ]
    else:
        cmd = [
            "ffprobe", "-v", "error", "-select_streams", stream_select,
            "-show_entries", f"stream={entry}", "-of", "default=noprint_wrappers=1:nokey=1",
            path,
        ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 or not result.stdout.strip():
        return None
    return result.stdout.strip().splitlines()[0]


def _sanitize_working_name(original_filename):
    """Never use a user-supplied filename as a filesystem path component --
    generate a random internal name and keep the original only for UI display.
    """
    ext = Path(original_filename).suffix.lower()
    safe_ext = ext if ext in (".mp4", ".mov", ".mkv", ".webm", ".avi", ".wav") else ""
    return f"{secrets.token_hex(8)}{safe_ext}"


def convert_video(video_path, reference_wav_path, output_dir, output_filename="output.mp4",
                   engine=ENGINE_OPENVOICE, elevenlabs_api_key=None, elevenlabs_voice_id=None):
    """Run the full validated pipeline. video_path/reference_wav_path are trusted
    local paths (already sanitized/saved by the caller, e.g. from an upload) --
    this function does the processing, not the upload handling.

    engine="openvoice" (default, free, local, CPU) requires reference_wav_path.
    engine="elevenlabs" (paid, requires the caller's own API key + voice_id) ignores
    reference_wav_path -- the target voice comes from the caller's ElevenLabs
    account instead of a reference clip, so reference_wav_path may be None.

    Runs entirely inside a per-job temp directory; only the final MP4 is copied to
    output_dir on success, and the temp directory (all intermediate WAVs) is always
    cleaned up afterward, success or failure.
    """
    start_time = time.time()
    warnings = []
    work_dir = tempfile.mkdtemp(prefix="voiceswap_")

    try:
        video_duration = float(_ffprobe_value(video_path, "v:0", "duration") or 0)
        video_frames_in = int(_ffprobe_value(video_path, "v:0", "nb_frames") or 0)
        if video_duration <= 0:
            raise PipelineError("Could not determine source video duration")

        # 1. Extract original audio
        extracted_audio = os.path.join(work_dir, "extracted.wav")
        _run_ffmpeg(["-i", video_path, "-vn", "-acodec", "pcm_s16le", extracted_audio],
                    "Audio extraction")
        source_y, source_sr = sf.read(extracted_audio)
        source_duration = len(source_y) / source_sr

        if reference_wav_path is not None:
            ref_y, ref_sr = sf.read(reference_wav_path)
            reference_duration = len(ref_y) / ref_sr
        else:
            reference_duration = 0.0

        # 2. Voice conversion
        conversion_start = time.time()
        converted_audio = os.path.join(work_dir, "converted.wav")
        if engine == ENGINE_OPENVOICE:
            if reference_wav_path is None:
                raise PipelineError("The openvoice engine requires a reference voice clip")
            cloner = VoiceCloner(engine=ENGINE_OPENVOICE)
            cloner.clone_voice(extracted_audio, reference_wav_path, converted_audio)
        elif engine == ENGINE_ELEVENLABS:
            raw_audio = os.path.join(work_dir, "elevenlabs_raw.audio")
            try:
                speech_to_speech(extracted_audio, raw_audio, elevenlabs_api_key, elevenlabs_voice_id)
            except ElevenLabsError as e:
                raise PipelineError(f"ElevenLabs conversion failed: {e}")
            # Normalize whatever ElevenLabs returned (typically MP3) to WAV so the
            # rest of the pipeline can treat every engine's output identically.
            _run_ffmpeg(["-i", raw_audio, converted_audio], "ElevenLabs output transcode")
        else:
            raise PipelineError(f"Unknown engine: {engine}")
        conversion_runtime = time.time() - conversion_start

        converted_y, converted_sr = sf.read(converted_audio)
        converted_duration_raw = len(converted_y) / converted_sr

        # 3. Pad converted audio to the video's exact duration (never trim video)
        padded_audio = os.path.join(work_dir, "padded.wav")
        _run_ffmpeg([
            "-i", converted_audio,
            "-af", f"apad,atrim=0:{video_duration}",
            "-ar", "48000",
            padded_audio,
        ], "Audio padding/resampling")

        # 4. Mux: untouched video + converted audio, AAC at 48kHz
        final_output = os.path.join(work_dir, "final.mp4")
        _run_ffmpeg([
            "-i", video_path,
            "-i", padded_audio,
            "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "copy",
            "-c:a", "aac", "-ar", "48000", "-ac", "2",
            # +faststart moves the moov atom to the front of the file. Without it,
            # mdat comes first and moov (the track index) comes last -- browsers
            # then have to read the whole file before they can properly resolve
            # tracks, which surfaced as video playing with no audio in st.video().
            "-movflags", "+faststart",
            final_output,
        ], "Final mux")

        # 5. Validate
        video_frames_out = int(_ffprobe_value(final_output, "v:0", "nb_frames") or 0)
        final_duration = float(_ffprobe_value(final_output, "format", "duration") or 0)
        video_start = _ffprobe_value(final_output, "v:0", "start_time")
        audio_start = _ffprobe_value(final_output, "a:0", "start_time")
        stream_start_times_match = video_start == audio_start

        if video_frames_out < video_frames_in:
            warnings.append(
                f"Output has fewer video frames than the source ({video_frames_out} vs "
                f"{video_frames_in}) -- the video may have been trimmed unexpectedly."
            )
        if not stream_start_times_match:
            warnings.append(
                f"Video/audio stream start times differ ({video_start}s vs {audio_start}s)."
            )

        # 6. Copy only the final MP4 out; everything else in work_dir is discarded
        os.makedirs(output_dir, exist_ok=True)
        final_dest = os.path.join(output_dir, output_filename)
        shutil.copy2(final_output, final_dest)

        return PipelineResult(
            output_video_path=final_dest,
            source_duration=source_duration,
            reference_duration=reference_duration,
            converted_duration_raw=converted_duration_raw,
            final_duration=final_duration,
            conversion_runtime_seconds=conversion_runtime,
            total_runtime_seconds=time.time() - start_time,
            engine=ENGINE,
            output_sample_rate=48000,
            video_frames_in=video_frames_in,
            video_frames_out=video_frames_out,
            stream_start_times_match=stream_start_times_match,
            warnings=warnings,
        )
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)
