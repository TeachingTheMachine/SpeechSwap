"""Optional premium voice engine: ElevenLabs Speech-to-Speech (Voice Changer) API.

Distinct from ElevenLabs' TTS API -- Speech-to-Speech takes audio in and returns
audio in the target voice, the same shape as the free local `openvoice` engine, so
it slots into the existing pipeline as an alternate conversion step rather than
requiring transcription or resynthesis. Requires a user-supplied API key and a
voice_id from that user's own ElevenLabs voice library; nothing here is free --
every call is billed to the caller's account (~$0.12/minute of source audio at the
time this was written).

The API key is only ever passed in memory for the duration of a single call. It is
never written to disk, logged, or included in the pipeline report.
"""

import os

import requests

API_BASE = "https://api.elevenlabs.io/v1"


class ElevenLabsError(Exception):
    pass


def list_voices(api_key, timeout=15):
    """Return [{"voice_id": ..., "name": ...}, ...] for the given account."""
    if not api_key:
        raise ElevenLabsError("No API key provided")
    try:
        response = requests.get(
            f"{API_BASE}/voices",
            headers={"xi-api-key": api_key},
            timeout=timeout,
        )
    except requests.RequestException as e:
        raise ElevenLabsError(f"Could not reach ElevenLabs: {e}")

    if response.status_code == 401:
        raise ElevenLabsError("ElevenLabs rejected this API key (401 Unauthorized).")
    if response.status_code != 200:
        raise ElevenLabsError(f"ElevenLabs API error {response.status_code}: {response.text[:300]}")

    voices = response.json().get("voices", [])
    return [{"voice_id": v["voice_id"], "name": v.get("name", v["voice_id"])} for v in voices]


def speech_to_speech(input_wav_path, output_audio_path, api_key, voice_id, timeout=180):
    """Send input_wav_path to ElevenLabs' Speech-to-Speech endpoint and write the
    raw response bytes (whatever encoding ElevenLabs returns, typically MP3) to
    output_audio_path. The caller is responsible for transcoding to WAV afterward --
    this function does not assume a container/codec.
    """
    if not api_key:
        raise ElevenLabsError("ElevenLabs engine requires an API key")
    if not voice_id:
        raise ElevenLabsError("ElevenLabs engine requires a voice ID")

    url = f"{API_BASE}/speech-to-speech/{voice_id}"
    headers = {"xi-api-key": api_key}

    with open(input_wav_path, "rb") as f:
        files = {"audio": (os.path.basename(input_wav_path), f, "audio/wav")}
        try:
            response = requests.post(url, headers=headers, files=files, timeout=timeout)
        except requests.RequestException as e:
            raise ElevenLabsError(f"ElevenLabs request failed: {e}")

    if response.status_code == 401:
        raise ElevenLabsError("ElevenLabs rejected this API key (401 Unauthorized).")
    if response.status_code != 200:
        raise ElevenLabsError(f"ElevenLabs API error {response.status_code}: {response.text[:300]}")

    with open(output_audio_path, "wb") as f:
        f.write(response.content)
