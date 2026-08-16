from collections import defaultdict
import re
from .models import Library
from .audio import load_audio, append_with_crossfade, normalize, change_speed
from .phonetics import phonemize, clean_word


def _tokenize(text: str) -> list[str]:
    return [clean_word(x) for x in re.findall(r"[A-Za-z']+", text) if clean_word(x)]


def _index(library: Library):
    phrases = defaultdict(list)
    words = defaultdict(list)
    phones = defaultdict(list)
    for s in library.segments:
        if s.kind == "phrase":
            phrases[tuple(s.text.lower().split())].append(s)
        elif s.kind == "word":
            words[s.text.lower()].append(s)
        elif s.kind == "phoneme" and s.phonemes:
            phones[s.phonemes[0]].append(s)
    return phrases, words, phones


def _best_phrase(tokens, pos, phrase_index, max_len=6):
    for n in range(min(max_len, len(tokens) - pos), 1, -1):
        key = tuple(tokens[pos:pos+n])
        candidates = phrase_index.get(key)
        if candidates:
            return max(candidates, key=lambda s: s.duration)
    return None


def generate(library: Library, text: str, speed: float = 1.0, crossfade_ms: float = 8.0, progress=None):
    if not library.segments:
        raise ValueError("The vocal library is empty. Analyze an acapella first.")
    phrase_index, word_index, phone_index = _index(library)
    tokens = _tokenize(text)
    if not tokens:
        raise ValueError("Enter some text to generate.")

    cache = {}
    parts = []
    sr = None
    i = 0
    while i < len(tokens):
        phrase = _best_phrase(tokens, i, phrase_index)
        if phrase is not None:
            chosen = [phrase]
            i += len(phrase.text.split())
        else:
            tok = tokens[i]
            candidates = word_index.get(tok, [])
            if candidates:
                chosen = [max(candidates, key=lambda s: s.duration)]
            else:
                chosen = []
                for phone in phonemize(tok):
                    pcs = phone_index.get(phone, [])
                    if pcs:
                        chosen.append(max(pcs, key=lambda s: s.duration))
            i += 1

        for seg in chosen:
            if progress:
                progress(f"Using {seg.kind}: {seg.text}")
            key = (seg.source, seg.start, seg.end)
            if key not in cache:
                audio, sr0 = load_audio(seg.source)
                if sr is None:
                    sr = sr0
                if sr0 != sr:
                    raise ValueError("Source vocals use different sample rates. Convert them to the same sample rate first.")
                a = int(max(0, round(seg.start * sr)))
                b = int(min(len(audio), round(seg.end * sr)))
                cache[key] = audio[a:b]
            parts.append(cache[key])

    if sr is None or not parts:
        raise ValueError("Could not find enough vocal material to construct the requested text.")
    output = append_with_crossfade(parts, sr, crossfade_ms)
    output = normalize(output)
    output = change_speed(output, speed)
    return output, sr
