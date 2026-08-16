# DK Rap Vocal Builder

A MorshuTalk-inspired rap vocal sentence synthesizer. Drop in an isolated acapella, let the application automatically transcribe and analyze it, then type new text and generate a vocal from the available recorded material.

## Intended workflow

1. Drop an acapella into the application.
2. The application transcribes it and performs phonetic/timing analysis automatically.
3. It builds a searchable local vocal library.
4. Type the sentence/lyrics you want.
5. Generate and preview the reconstructed vocal.
6. Export the result as WAV.

The generator prioritizes larger natural recordings when possible (phrase -> word -> syllable -> phoneme) and falls back to smaller units when necessary.

## Status

Early project scaffold. The first implementation will focus on automatic corpus analysis and basic text-to-vocal concatenation before adding advanced rap timing and pitch controls.

## Planned stack

- Python
- Local speech-to-text
- Forced alignment / phoneme timing
- Grapheme-to-phoneme conversion
- Local audio processing
- Desktop GUI
- PyInstaller Windows packaging

## Legal / source audio

Only use vocal recordings you have the right to process and redistribute. The application itself does not ship copyrighted source vocals.
