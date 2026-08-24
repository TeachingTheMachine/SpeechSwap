# SpeechSwap Voice Conversion

Swaps the voice in a video for a different one, keeping the original video and its
exact timing untouched. No text-to-speech resynthesis, no lip-sync regeneration --
voice conversion works on the audio waveform directly, so the mouth in the source
video already matches the output.

Runs entirely on your own Windows machine. No GPU required, no cloud hosting, and
the default path has no per-use cost.

## Demo

<video src="https://raw.githubusercontent.com/TeachingTheMachine/SpeechSwap/main/voice_swap_demo/assets/prerendered_example.mp4" controls width="480"></video>

(If the player above doesn't render, the file is at
[`assets/prerendered_example.mp4`](assets/prerendered_example.mp4).)

This is a real run of the pipeline below against
[`assets/demo_video.mp4`](assets/demo_video.mp4) and a bundled synthetic reference
voice -- not a hand-picked or edited result.

## How it works

```
video in -> extract audio -> voice conversion -> pad to source duration -> mux with
            (ffmpeg)          (openvoice, CPU)     (never trims video)     original video
```

Voice conversion preserves timing by construction, which is what makes the lip-sync
problem disappear: the output audio is exactly as long as the input audio was
supposed to be, matched to the original video, so there's no re-timing step to get
wrong.

Every ffmpeg flag in `pipeline.py` was arrived at by testing against a real source
file, not assumed -- see the module docstring for the two non-obvious ones (why
there's no `-avoid_negative_ts`, and why audio is padded rather than using
`-shortest` to trim video).

## Setup

Requires [ffmpeg](https://ffmpeg.org/) on your `PATH` and Python 3.10+.

```
setup.bat
```

This creates a `.venv`, installs pinned dependencies, and downloads + verifies the
voice-conversion model (a one-time ~130MB download, checked against a pinned
revision and sha256 hash -- see `checkpoint_manager.py`).

## Run

```
run_demo.bat
```

Opens the app at `http://localhost:8501`. Two modes:

- **Run Demo** -- runs the real pipeline against the bundled sample video and a
  voice you pick from four bundled options, live, not a canned result.
- **Custom Mode** -- upload your own video and either pick a bundled voice, upload
  your own reference clip, or use ElevenLabs (see below). Requires checking a
  consent box confirming you have the right to use the reference voice before the
  Convert button becomes clickable.

## Optional: ElevenLabs premium voices

The free path (`openvoice`, local, CPU) is the default. If you have an
[ElevenLabs](https://elevenlabs.io) account, you can instead convert through their
Speech-to-Speech API for higher-quality output, using your own API key and your own
voice library. This is a real, billed API call (ElevenLabs' published rate is about
$0.12/minute of source audio at the time this was written) -- there is nothing free
about this path.

To use it, copy `.env.example` to `.env` and fill in:

```
ELEVENLABS_API_KEY=your_key_here
```

`.env` is gitignored and only ever read locally, in memory, for the current session
-- it's never written back to disk or included in the run report. In Custom Mode,
choose "ElevenLabs (paid, your API key)" as the voice source, click "Load my
ElevenLabs voices," and pick one.

## Limitations (v1, by design)

- Works best on short clips with one clearly audible speaker.
- Multiple speakers in a source video all get converted to the same single target
  voice -- there's no speaker separation.
- Background music or noise may produce artifacts, since there's no source
  separation step.
- CPU-only. Runs faster than real time on a normal laptop CPU for the free engine,
  so GPU support isn't needed and isn't implemented.

## Project structure

```
app.py                 Streamlit UI: Run Demo tab, Custom Mode tab, results
pipeline.py             extract -> convert -> pad -> mux -> validate
elevenlabs_engine.py    optional ElevenLabs Speech-to-Speech engine
checkpoint_manager.py   downloads + verifies the pinned openvoice model
report.py               builds the per-run JSON validation report
assets/                 bundled demo video, reference voices, pre-rendered example
outputs/                gitignored -- where your results get saved
setup.bat               one-time environment + model setup
run_demo.bat            launches the app
requirements.txt        every dependency pinned to an exact version
```

Every run writes a `report.json` next to its output video recording engine used,
durations, frame counts, and validation checks (frame count preserved, audio/video
stream start times aligned) -- so a result's correctness doesn't have to be taken on
faith.
