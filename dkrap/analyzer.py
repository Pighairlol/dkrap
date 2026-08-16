from pathlib import Path
from .models import Library, Segment
from .phonetics import phonemize, clean_word, _ensure_nltk_data


def _approximate_phoneme_segments(word_start: float, word_end: float, phones: list[str]):
    if not phones:
        return []
    weights = [max(1, sum(ch.isalpha() for ch in p)) for p in phones]
    total = float(sum(weights))
    t = word_start
    out = []
    for p, w in zip(phones, weights):
        d = (word_end - word_start) * (w / total)
        out.append((p, t, t + d))
        t += d
    return out


def _add_phrase_segments(segments, word_entries, source, next_id):
    for start_idx in range(len(word_entries)):
        for length in range(2, 7):
            end_idx = start_idx + length
            if end_idx > len(word_entries):
                break
            window = word_entries[start_idx:end_idx]
            gaps = [window[i + 1].start - window[i].end for i in range(len(window) - 1)]
            if any(gap < -0.02 or gap > 0.65 for gap in gaps):
                continue
            text = " ".join(s.text for s in window)
            phones = []
            for s in window:
                phones.extend(s.phonemes)
            segments.append(Segment(next_id, source, window[0].start, window[-1].end, text, "phrase", phones))
            next_id += 1
    return next_id


def analyze_files(paths: list[str], model_name: str = "tiny.en", progress=None) -> Library:
    try:
        from faster_whisper import WhisperModel
    except Exception as exc:
        raise RuntimeError("faster-whisper is required for automatic analysis. Install dependencies first.") from exc

    _ensure_nltk_data()
    import torch
    device = "cuda" if torch.cuda.is_available() else "cpu"
    compute_type = "float16" if device == "cuda" else "int8"

    if progress:
        progress(f"Loading transcription model ({model_name}, {device})")
    model = WhisperModel(model_name, device=device, compute_type=compute_type)

    segments = []
    sid = 0
    for index, source in enumerate(paths, 1):
        if progress:
            progress(f"Transcribing {Path(source).name} ({index}/{len(paths)})")
        try:
            results, _info = model.transcribe(source, language="en", word_timestamps=True, vad_filter=False, beam_size=5)
            results = list(results)
        except Exception as exc:
            raise RuntimeError(f"Could not transcribe {Path(source).name}: {exc}") from exc

        file_words = []
        for result_segment in results:
            for word_info in (getattr(result_segment, "words", None) or []):
                text = clean_word(word_info.word or "")
                start = word_info.start
                end = word_info.end
                if not text or start is None or end is None or end <= start:
                    continue
                phones = phonemize(text)
                seg = Segment(sid, str(source), float(start), float(end), text, "word", phones)
                segments.append(seg)
                file_words.append(seg)
                sid += 1
                for phone, ps, pe in _approximate_phoneme_segments(float(start), float(end), phones):
                    segments.append(Segment(sid, str(source), ps, pe, text, "phoneme", [phone]))
                    sid += 1

        sid = _add_phrase_segments(segments, file_words, str(source), sid)
        if progress:
            progress(f"Indexed {len(file_words)} words from {Path(source).name}")

    return Library(audio_files=[str(p) for p in paths], segments=segments, model_name=model_name)
