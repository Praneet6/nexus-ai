"""
F04 — Empathy Mirroring
Classifies user writing style across 5 axes and adapts Claude's tone in real-time.
"""
import re
from dataclasses import dataclass
from typing import Optional

try:
    import spacy
    _nlp = None

    def get_nlp():
        global _nlp
        if _nlp is None:
            try:
                _nlp = spacy.load("en_core_web_sm")
            except Exception:
                _nlp = None
        return _nlp
except ImportError:
    def get_nlp():
        return None


@dataclass
class StyleProfile:
    formality: str = "casual"          # formal | casual | slang
    verbosity: str = "balanced"        # terse | balanced | verbose
    punctuation: str = "standard"      # heavy | standard | minimal
    emotional_tone: str = "neutral"    # expressive | neutral | restrained
    vocab_grade: str = "intermediate"  # simple | intermediate | advanced

    def to_dict(self) -> dict:
        return {
            "formality": self.formality,
            "verbosity": self.verbosity,
            "punctuation": self.punctuation,
            "emotional_tone": self.emotional_tone,
            "vocab_grade": self.vocab_grade,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "StyleProfile":
        return cls(
            formality=data.get("formality", "casual"),
            verbosity=data.get("verbosity", "balanced"),
            punctuation=data.get("punctuation", "standard"),
            emotional_tone=data.get("emotional_tone", "neutral"),
            vocab_grade=data.get("vocab_grade", "intermediate"),
        )


SLANG_WORDS = {
    "lol", "omg", "btw", "tbh", "ngl", "idk", "gonna", "wanna", "gotta",
    "kinda", "sorta", "ya", "yep", "nope", "ugh", "meh", "asap", "fyi",
    "imo", "smh", "brb", "afaik", "iirc", "rn", "atm", "tbf", "gr8", "thx",
}

FORMAL_MARKERS = {
    "therefore", "however", "furthermore", "regarding", "kindly", "herewith",
    "accordingly", "notwithstanding", "pursuant", "aforementioned", "henceforth",
    "respectfully", "sincerely", "cordially", "attached", "enclosed",
}

EMOTION_POSITIVE = {"great", "amazing", "wonderful", "fantastic", "love", "excellent", "perfect", "awesome"}
EMOTION_NEGATIVE = {"terrible", "horrible", "awful", "disgusting", "furious", "angry", "upset", "frustrated", "hate"}
EMOTION_WORDS = EMOTION_POSITIVE | EMOTION_NEGATIVE


def classify_style(messages: list[str]) -> StyleProfile:
    """Classify writing style from last 3 user messages. <10ms via heuristics."""
    if not messages:
        return StyleProfile()

    text = " ".join(messages[-3:])
    words = re.findall(r"\b\w+\b", text.lower())
    sentences = re.split(r"[.!?]+", text)
    sentences = [s.strip() for s in sentences if s.strip()]

    if not words:
        return StyleProfile()

    word_count = len(words)
    sentence_count = max(len(sentences), 1)

    # --- Formality ---
    slang_count = sum(1 for w in words if w in SLANG_WORDS)
    formal_count = sum(1 for w in words if w in FORMAL_MARKERS)
    slang_ratio = slang_count / word_count
    formal_ratio = formal_count / word_count

    if slang_ratio > 0.04 or slang_count >= 2:
        formality = "slang"
    elif formal_ratio > 0.02 or formal_count >= 2:
        formality = "formal"
    else:
        # Check capitalisation — formal users tend to capitalise properly
        cap_words = sum(1 for w in text.split() if w and w[0].isupper() and len(w) > 1)
        cap_ratio = cap_words / max(len(text.split()), 1)
        formality = "formal" if cap_ratio > 0.3 else "casual"

    # --- Verbosity ---
    avg_words_per_sentence = word_count / sentence_count
    if avg_words_per_sentence < 8:
        verbosity = "terse"
    elif avg_words_per_sentence > 20:
        verbosity = "verbose"
    else:
        verbosity = "balanced"

    # --- Punctuation ---
    punct_chars = sum(1 for c in text if c in ".,;:!?-—()[]")
    punct_ratio = punct_chars / max(word_count, 1)
    if punct_ratio > 0.3:
        punctuation = "heavy"
    elif punct_ratio < 0.1:
        punctuation = "minimal"
    else:
        punctuation = "standard"

    # --- Emotional Tone ---
    exclamation_count = text.count("!")
    emotion_count = sum(1 for w in words if w in EMOTION_WORDS)
    exclamation_ratio = exclamation_count / sentence_count

    if exclamation_ratio > 0.5 or emotion_count >= 2:
        emotional_tone = "expressive"
    elif exclamation_count == 0 and emotion_count == 0:
        emotional_tone = "restrained"
    else:
        emotional_tone = "neutral"

    # --- Vocabulary Grade ---
    avg_word_len = sum(len(w) for w in words) / max(word_count, 1)
    if avg_word_len < 4.5:
        vocab_grade = "simple"
    elif avg_word_len > 6.5:
        vocab_grade = "advanced"
    else:
        vocab_grade = "intermediate"

    return StyleProfile(
        formality=formality,
        verbosity=verbosity,
        punctuation=punctuation,
        emotional_tone=emotional_tone,
        vocab_grade=vocab_grade,
    )


def build_style_prompt_suffix(profile: StyleProfile) -> str:
    """Generate Claude prompt suffix to match user's communication style."""
    lines = ["\n[STYLE MIRROR — Adapt your entire response to match this user's communication style]"]

    # Formality
    if profile.formality == "slang":
        lines.append("• Use casual, friendly language. Contractions, abbreviations, and informal phrasing are totally fine.")
    elif profile.formality == "formal":
        lines.append("• Use professional, formal language. Complete sentences, proper grammar, and respectful tone.")
    else:
        lines.append("• Use a friendly but clear conversational tone — not too formal, not too casual.")

    # Verbosity
    if profile.verbosity == "terse":
        lines.append("• Be brief and direct. Match the user's concise style — avoid long paragraphs.")
    elif profile.verbosity == "verbose":
        lines.append("• Provide thorough, detailed responses — this user appreciates comprehensive explanations.")
    else:
        lines.append("• Keep responses moderate in length — detailed enough but not overwhelming.")

    # Emotional tone
    if profile.emotional_tone == "expressive":
        lines.append("• The user is emotionally engaged. Acknowledge their feelings explicitly before solving anything.")
    elif profile.emotional_tone == "restrained":
        lines.append("• Keep an even, measured tone — this user prefers facts over emotional language.")

    # Vocabulary
    if profile.vocab_grade == "simple":
        lines.append("• Use simple, everyday words. Avoid jargon and technical terms unless necessary.")
    elif profile.vocab_grade == "advanced":
        lines.append("• This user is articulate — you can use precise, sophisticated vocabulary.")

    return "\n".join(lines)
