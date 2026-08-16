from pathlib import Path
import numpy as np
import soundfile as sf


def load_audio(path: str | Path):
    audio, sr = sf.read(str(path), dtype="float32", always_2d=False)
    if audio.ndim > 1:
        audio = np.mean(audio, axis=1)
    return audio.astype(np.float32), int(sr)


def normalize(audio: np.ndarray, peak: float = 0.98) -> np.ndarray:
    if audio.size == 0:
        return audio
    m = float(np.max(np.abs(audio)))
    if m < 1e-8:
        return audio
    return audio * (peak / m)


def append_with_crossfade(parts: list[np.ndarray], sr: int, crossfade_ms: float = 8.0) -> np.ndarray:
    if not parts:
        return np.zeros(0, dtype=np.float32)
    out = parts[0].astype(np.float32, copy=True)
    fade = max(0, int(sr * crossfade_ms / 1000.0))
    for part in parts[1:]:
        part = part.astype(np.float32, copy=False)
        if fade <= 0 or len(out) < fade or len(part) < fade:
            out = np.concatenate([out, part])
            continue
        a = np.linspace(1.0, 0.0, fade, dtype=np.float32)
        b = 1.0 - a
        mixed = out[-fade:] * a + part[:fade] * b
        out = np.concatenate([out[:-fade], mixed, part[fade:]])
    return out


def change_speed(audio: np.ndarray, speed: float) -> np.ndarray:
    if speed <= 0:
        raise ValueError("Speed must be positive")
    if abs(speed - 1.0) < 1e-4 or audio.size == 0:
        return audio
    new_len = max(1, int(round(len(audio) / speed)))
    x_old = np.linspace(0.0, 1.0, len(audio), endpoint=False)
    x_new = np.linspace(0.0, 1.0, new_len, endpoint=False)
    return np.interp(x_new, x_old, audio).astype(np.float32)


def write_wav(path: str | Path, audio: np.ndarray, sr: int) -> None:
    sf.write(str(path), audio, sr, subtype="PCM_16")
