# DK Rap Vocal Builder

A MorshuTalk-inspired rap vocal sentence synthesizer.

## Current workflow

1. Open the app.
2. Select one or more isolated acapellas.
3. Click **Analyze Vocals**.
4. The app automatically transcribes the vocals, extracts word timestamps, phonemizes the words, and builds phrase/word/phoneme segments.
5. Type arbitrary text.
6. Click **GENERATE**.
7. Export the result as WAV.

The generator prioritizes **phrase -> word -> phoneme** material, preserving larger natural recordings whenever the requested text exists in the source corpus.

## Why this version does not use WhisperX

The MVP only needs transcription plus word timestamps. It uses Faster-Whisper directly, avoiding Pyannote VAD, TorchCodec/FFmpeg setup, and WhisperX alignment initialization. This makes the Windows setup substantially smaller and more reliable.

Phoneme timestamps are currently approximated across each word. This is deliberate for the first working version; a later version can add true forced phoneme alignment once the basic sentence builder is proven.

## Windows development

```bat
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
python main.py
```

The first transcription run downloads the selected Faster-Whisper model automatically.

## Build the EXE

```bat
pip install pyinstaller
pyinstaller DKRapBuilder.spec
```

The GitHub Actions workflow also builds a Windows artifact automatically on pushes to `main` and on manual workflow runs.

Only use source recordings you have the right to process and redistribute.
