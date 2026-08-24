"""Builds the per-run JSON validation report."""

import json
import os
from datetime import datetime, timezone

from checkpoint_manager import PINNED_REVISION

APP_VERSION = "0.1.0"


def build_report(pipeline_result, consent=None):
    """consent: None for Demo Mode (bundled, pre-authorized asset, no user attestation
    needed), or {"confirmed": bool, "timestamp": str} for Custom Mode.
    """
    timing_difference = abs(pipeline_result.final_duration - pipeline_result.source_duration)

    report = {
        "app_version": APP_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "engine": pipeline_result.engine,
        # PINNED_REVISION identifies the local openvoice checkpoint -- not meaningful
        # for the ElevenLabs cloud engine, which has no local model to pin.
        "model_revision": PINNED_REVISION if pipeline_result.engine == "openvoice" else None,
        "source_duration_seconds": round(pipeline_result.source_duration, 4),
        "reference_duration_seconds": round(pipeline_result.reference_duration, 4),
        "converted_duration_raw_seconds": round(pipeline_result.converted_duration_raw, 4),
        "final_duration_seconds": round(pipeline_result.final_duration, 4),
        "timing_difference_seconds": round(timing_difference, 4),
        "conversion_runtime_seconds": round(pipeline_result.conversion_runtime_seconds, 3),
        "total_runtime_seconds": round(pipeline_result.total_runtime_seconds, 3),
        "output_sample_rate_hz": pipeline_result.output_sample_rate,
        "video_frames_in": pipeline_result.video_frames_in,
        "video_frames_out": pipeline_result.video_frames_out,
        "frame_count_matches": pipeline_result.video_frames_in == pipeline_result.video_frames_out,
        "stream_start_times_match": pipeline_result.stream_start_times_match,
        "validation_status": "pass" if not pipeline_result.warnings else "warnings",
        "warnings": pipeline_result.warnings,
        "output_video_path": pipeline_result.output_video_path,
    }

    if consent is not None:
        report["consent"] = consent

    return report


def write_report(report, output_dir, filename="report.json"):
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, filename)
    with open(path, "w") as f:
        json.dump(report, f, indent=2)
    return path
