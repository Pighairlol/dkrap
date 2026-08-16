from functools import lru_cache

try:
    from g2p_en import G2p
except Exception:
    G2p = None


def _ensure_nltk_data() -> None:
    import nltk
    resources = {
        "taggers/averaged_perceptron_tagger_eng": "averaged_perceptron_tagger_eng",
        "corpora/cmudict": "cmudict",
    }
    for resource_path, package in resources.items():
        try:
            nltk.data.find(resource_path)
        except LookupError:
            nltk.download(package, quiet=True)


@lru_cache(maxsize=1)
def _g2p():
    if G2p is None:
        raise RuntimeError("g2p-en is not installed")
    _ensure_nltk_data()
    return G2p()


def phonemize(text: str) -> list[str]:
    phonemes = []
    for p in _g2p()(text):
        p = str(p).strip()
        if not p or p in {" ", "_"}:
            continue
        phonemes.append(p)
    return phonemes


def clean_word(text: str) -> str:
    return "".join(ch.lower() for ch in text if ch.isalpha() or ch == "'")
