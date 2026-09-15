"""Text preprocessing utilities.

Responsibilities (per Trello card Fase 1):
  * lowercase
  * stopword removal
  * cleaning (punctuation, digits, whitespace normalization)

All functions are module-level (no lambdas) so the full sklearn Pipeline —
including this preprocessing step — can be serialized with joblib.
"""
from __future__ import annotations

import re

from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

STOPWORDS: frozenset[str] = frozenset(ENGLISH_STOP_WORDS)

# Matches anything that is not a lowercase ASCII letter or whitespace.
_NON_ALPHA_RE = re.compile(r"[^a-z\s]")
# Collapses runs of whitespace into a single space.
_WHITESPACE_RE = re.compile(r"\s+")


def clean_text(text: str) -> str:
    """Lowercase, strip punctuation/digits and normalize whitespace."""
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = _NON_ALPHA_RE.sub(" ", text)
    return _WHITESPACE_RE.sub(" ", text).strip()


def remove_stopwords(text: str) -> str:
    """Remove English stopwords from a space-separated string."""
    return " ".join(tok for tok in text.split() if tok not in STOPWORDS)


def preprocess(text: str) -> str:
    """Full preprocessing: clean + remove stopwords."""
    return remove_stopwords(clean_text(text))


def preprocess_texts(texts) -> list[str]:
    """Apply full preprocessing to an iterable of raw texts.

    Kept as a named function (picklable) so it can be wrapped by
    ``sklearn.preprocessing.FunctionTransformer`` inside the serialized model.
    """
    return [preprocess(t) for t in texts]
