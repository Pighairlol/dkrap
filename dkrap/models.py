from dataclasses import dataclass, asdict
from pathlib import Path
import json

@dataclass
class Segment:
    id: int
    source: str
    start: float
    end: float
    text: str
    kind: str
    phonemes: list[str]

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)

@dataclass
class Library:
    audio_files: list[str]
    segments: list[Segment]
    language: str = "en"
    model_name: str = "tiny.en"

    def save(self, path: Path) -> None:
        payload = {
            "audio_files": self.audio_files,
            "segments": [asdict(s) for s in self.segments],
            "language": self.language,
            "model_name": self.model_name,
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "Library":
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            audio_files=data["audio_files"],
            segments=[Segment(**s) for s in data["segments"]],
            language=data.get("language", "en"),
            model_name=data.get("model_name", "tiny.en"),
        )
