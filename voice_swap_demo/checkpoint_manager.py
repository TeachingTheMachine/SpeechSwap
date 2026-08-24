"""Downloads and verifies the pinned OpenVoice v2 checkpoint used by this app.

KNOWN LIMITATION: voiceclonnx's own public API (OpenVoiceV2Adapter) calls
huggingface_hub.hf_hub_download(repo_id=..., filename=...) internally with no
revision parameter -- confirmed by reading its source. It always resolves to
the repo's current `main` branch; there is no way to force it to use a specific
pinned commit through voiceclonnx's own API. What this module *can* guarantee:
downloading and sha256-verifying the exact files at the pinned revision below,
so setup fails loudly if the upstream repo's content has changed unexpectedly,
and so the model is warm in the local HF cache before the app's first real run.
If upstream `main` moves to a new commit after this was written, voiceclonnx's
own internal fetch will use that newer version, not this pinned one -- a real
gap in the upstream library, documented here rather than silently assumed away.
"""

import hashlib

from huggingface_hub import hf_hub_download

HF_REPO_ID = "TigreGotico/voiceclonnx-openvoice-v2"
PINNED_REVISION = "34d010c192c97f763207f488f6057fd07fee42ad"

# Verified by direct download + sha256sum during this project's validation spike.
CHECKPOINT_FILES = {
    "tone_converter.onnx": {
        "sha256": "7d7ee834c230037ead5cd6b64d44fcd842fbab5cd4cf6fe3ab381fad763325e9",
        "size_bytes": 128_051_288,
    },
    "tone_ref_encoder.onnx": {
        "sha256": "3dd4918cab90e1acf7fa5c6f7539c27710e7a3cdfba550468c5ea49399178bf7",
        "size_bytes": 3_259_275,
    },
}


class CheckpointVerificationError(Exception):
    pass


def _sha256_of(path):
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_and_verify(progress_callback=None):
    """Download each pinned checkpoint file and verify its sha256. Raises
    CheckpointVerificationError on any mismatch. Returns the list of local paths.
    """
    paths = []
    for filename, expected in CHECKPOINT_FILES.items():
        if progress_callback:
            progress_callback(f"Downloading {filename} ({expected['size_bytes'] / 1e6:.0f} MB)...")

        local_path = hf_hub_download(
            repo_id=HF_REPO_ID, filename=filename, revision=PINNED_REVISION,
        )

        actual_hash = _sha256_of(local_path)
        if actual_hash != expected["sha256"]:
            raise CheckpointVerificationError(
                f"{filename}: sha256 mismatch. Expected {expected['sha256']}, "
                f"got {actual_hash}. The pinned checkpoint may have changed upstream "
                f"or the download was corrupted."
            )
        paths.append(local_path)

    return paths


def is_verified():
    """Check whether all pinned checkpoint files are already present and valid,
    without re-downloading. Used by the launch script to fail fast with a clear
    message instead of silently re-downloading on every run.
    """
    try:
        for filename, expected in CHECKPOINT_FILES.items():
            local_path = hf_hub_download(
                repo_id=HF_REPO_ID, filename=filename, revision=PINNED_REVISION,
                local_files_only=True,
            )
            if _sha256_of(local_path) != expected["sha256"]:
                return False
        return True
    except Exception:
        return False


if __name__ == "__main__":
    def _print_progress(msg):
        print(msg)

    try:
        download_and_verify(progress_callback=_print_progress)
        print("All checkpoints downloaded and verified successfully.")
    except CheckpointVerificationError as e:
        print(f"CHECKPOINT VERIFICATION FAILED: {e}")
        raise SystemExit(1)
