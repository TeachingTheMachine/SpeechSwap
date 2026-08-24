# SpeechSwap

Replaces the voice in a video with a different one. This repo has two apps, built in
that order:

## [`voice_swap_demo/`](voice_swap_demo/) -- current, recommended

A local Windows desktop app using voice conversion instead of text-to-speech. You
give it a video and a target voice; it converts the original audio directly,
preserving exact timing, so there's no lip-sync problem to solve. Runs on CPU, no
GPU or cloud hosting required, free by default with an optional ElevenLabs
premium-voice path if you bring your own API key.

See [`voice_swap_demo/README.md`](voice_swap_demo/README.md) for the demo video,
setup, and how it works.

## SpeechSwap Web -- the original approach

The app this repo started as: a browser-based Streamlit tool (`simple_app.py`) that
generates new speech with OpenAI's TTS API and time-stretches it to match the
source video's duration, using FFmpeg's `atempo` filter with pause-aware stretching
to keep timing natural.

```
streamlit run simple_app.py
```

Requires an OpenAI API key (`OPENAI_API_KEY`) for TTS generation; FFmpeg for audio
extraction, stretching, and remuxing.

**Components:**
- `simple_app.py` -- Streamlit UI: upload, script input, voice selection, processing
- `video_processor.py` -- audio extraction, stretch-based synchronization, remux
- `basic_tts_generator.py` -- OpenAI TTS integration, six built-in voices

**How it stretches audio to fit:** computes the ratio between generated-audio
duration and video duration, then applies FFmpeg's `atempo` filter (chained when the
ratio falls outside `atempo`'s single-filter range) to compress or stretch the
generated speech to match exactly. An optional pause-aware mode preserves natural
breathing gaps rather than stretching them uniformly.

**Known limitation:** since this path generates new speech rather than converting
the original audio, the source video's lip movements no longer match the new audio
-- there's no lip-sync step. `voice_swap_demo/` exists specifically because voice
conversion sidesteps this problem rather than trying to solve it.

---

`AGENT_CONVERSATION.md` at the repo root is a working log from the design process
behind `voice_swap_demo/` -- research, spike tests, and the reasoning behind each
architectural decision, if you want the "why" behind the current approach.
