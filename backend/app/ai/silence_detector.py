"""
F02 — Silence Detection
Reads typing hesitation metadata (NOT key characters) to detect emotional state.

Model: DecisionTreeClassifier trained on synthetic keystroke timing data.
If the model artifact is missing at startup, train_if_missing() retrains it
automatically so a fresh clone always works without manual setup.
"""
import os
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

# ── Model path ────────────────────────────────────────────────────────────────
# Resolved relative to this file so it works regardless of CWD.
# Override via MODEL_PATH env var (e.g. for Docker volume mounts).
_DEFAULT_MODEL_PATH = os.path.join(
    os.path.dirname(__file__),   # backend/app/ai/
    "..", "models",              # backend/app/models/
    "silence_model.joblib",
)
MODEL_PATH: str = os.environ.get("MODEL_PATH") or os.path.normpath(_DEFAULT_MODEL_PATH)

# Lazy-loaded model singleton
_model = None


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class KeystrokeData:
    delay_ms: float       # ms since last keypress (NOT which key)
    is_backspace: bool    # deletion event?
    idle_ms: float        # idle time before this key


@dataclass
class SilenceResult:
    state: str            # "confident" | "confused" | "distressed"
    confidence: float     # 0.0 → 1.0
    signals: dict         # raw metrics for transparency


# ── Model management ──────────────────────────────────────────────────────────

def _extract_features(keydata: list[dict]) -> list[float]:
    """
    Convert raw keystroke event list to the 4-feature vector the model expects:
    [backspace_ratio, avg_delay_ms, long_idle_count, max_idle_ms]
    """
    total_keys = len(keydata)
    backspace_count = sum(1 for k in keydata if k.get("is_backspace", False))
    delays = [k.get("delay_ms", 0) for k in keydata if k.get("delay_ms", 0) > 0]
    idles = [k.get("idle_ms", 0) for k in keydata]

    backspace_ratio = backspace_count / max(total_keys, 1)
    avg_delay = sum(delays) / max(len(delays), 1)
    long_idle_count = sum(1 for i in idles if i > 2000)
    max_idle = max(idles) if idles else 0.0

    return [backspace_ratio, avg_delay, long_idle_count, max_idle]


def _run_training(model_path: str) -> bool:
    """
    Train the silence classifier in-process and save the artifact.
    Uses the same data-generation and training logic as ml/train_silence_model.py
    but runs without spawning a subprocess, so it respects the current
    Python environment and doesn't need ml/ to be on sys.path.

    Returns True on success, False on any failure.
    """
    try:
        import numpy as np
        from sklearn.tree import DecisionTreeClassifier
        import joblib

        logger.info("[F02] Training silence detection model from synthetic data…")

        rng = np.random.default_rng(42)
        n = 1500  # slightly larger than the standalone script for better coverage
        X, y = [], []

        for _ in range(n):
            state = rng.choice(["confident", "confused", "distressed"])
            if state == "confident":
                row = [
                    rng.uniform(0.0, 0.15),    # backspace_ratio
                    rng.uniform(80.0, 180.0),  # avg_delay_ms
                    int(rng.poisson(0.2)),      # long_idle_count
                    rng.uniform(0.0, 1500.0),  # max_idle_ms
                ]
            elif state == "confused":
                row = [
                    rng.uniform(0.15, 0.35),
                    rng.uniform(180.0, 300.0),
                    int(rng.poisson(1.5)),
                    rng.uniform(1500.0, 4500.0),
                ]
            else:  # distressed
                row = [
                    rng.uniform(0.35, 0.70),
                    rng.uniform(300.0, 600.0),
                    int(rng.poisson(3.5)),
                    rng.uniform(4500.0, 12000.0),
                ]
            X.append(row)
            y.append(state)

        clf = DecisionTreeClassifier(max_depth=4, random_state=42)
        clf.fit(np.array(X), y)

        # Ensure destination directory exists
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        joblib.dump(clf, model_path)

        logger.info(f"[F02] Model saved → {model_path}")
        return True

    except Exception as exc:
        logger.error(f"[F02] Training failed: {exc}")
        return False


def train_if_missing(model_path: str = MODEL_PATH) -> bool:
    """
    Check whether the model artifact exists; train it if not.

    Called from main.py lifespan so every fresh clone auto-bootstraps.
    Returns True if the model is ready (existed or was just trained),
    False if training failed.
    """
    if os.path.exists(model_path):
        logger.info(f"[F02] Model found at {model_path} — skipping training")
        return True
    logger.info(f"[F02] Model not found at {model_path} — starting training…")
    return _run_training(model_path)


def load_model(model_path: str = MODEL_PATH):
    """Lazy-load the trained classifier (singleton, thread-safe under GIL)."""
    global _model
    if _model is not None:
        return _model
    try:
        import joblib
        _model = joblib.load(model_path)
        logger.info("[F02] Silence model loaded from disk")
    except Exception as exc:
        logger.warning(f"[F02] Could not load model ({exc}) — falling back to heuristics")
        _model = None
    return _model


# ── Classifier ────────────────────────────────────────────────────────────────

def classify_silence(keydata: list[dict]) -> SilenceResult:
    """
    Classify user emotional state from typing metadata.
    Privacy: only timing signals, never key characters.

    Strategy:
      1. If the trained model is available → use it (more accurate).
      2. Otherwise → fall back to the score-based heuristic (always works).
    """
    if not keydata or len(keydata) < 3:
        return SilenceResult(state="confident", confidence=0.5, signals={})

    features = _extract_features(keydata)
    backspace_ratio, avg_delay, long_idle_count, max_idle = features

    signals = {
        "backspace_ratio": round(backspace_ratio, 3),
        "avg_delay_ms": round(avg_delay, 1),
        "long_idle_count": int(long_idle_count),
        "max_idle_ms": max_idle,
        "total_keystrokes": len(keydata),
    }

    # ── Path 1: ML model ──────────────────────────────────────
    clf = load_model()
    if clf is not None:
        try:
            import numpy as np
            proba = clf.predict_proba([features])[0]
            classes = list(clf.classes_)
            state = classes[int(proba.argmax())]
            confidence = round(float(proba.max()), 3)
            signals["classifier"] = "ml_model"
            signals["score"] = None
            return SilenceResult(state=state, confidence=confidence, signals=signals)
        except Exception as exc:
            logger.warning(f"[F02] Model inference failed, using heuristics: {exc}")

    # ── Path 2: Heuristic fallback ────────────────────────────
    score = 0.0
    if backspace_ratio > 0.4:
        score += 3.0
    elif backspace_ratio > 0.2:
        score += 1.5
    if long_idle_count >= 3:
        score += 2.5
    elif long_idle_count >= 1:
        score += 1.0
    if max_idle > 8000:
        score += 2.0
    elif max_idle > 4000:
        score += 1.0
    if avg_delay > 400:
        score += 1.0
    elif avg_delay > 250:
        score += 0.5

    if score >= 5.0:
        state = "distressed"
        confidence = min(0.95, 0.6 + (score - 5.0) * 0.05)
    elif score >= 2.5:
        state = "confused"
        confidence = min(0.9, 0.5 + (score - 2.5) * 0.08)
    else:
        state = "confident"
        confidence = min(0.95, 0.7 + (2.5 - score) * 0.1)

    signals["classifier"] = "heuristic"
    signals["score"] = round(score, 2)
    return SilenceResult(state=state, confidence=round(confidence, 3), signals=signals)


# ── Claude prompt hint ────────────────────────────────────────────────────────

def get_silence_response_hint(state: str) -> Optional[str]:
    """Generate Claude prompt modifier based on detected emotional state."""
    if state == "distressed":
        return (
            "[SILENCE ALERT — DISTRESSED] The user showed significant typing hesitation "
            "(heavy backspacing and long pauses). Open your response by gently acknowledging "
            "that this might be hard to put into words. Be extra warm and patient. "
            "Do NOT immediately jump to troubleshooting — create emotional safety first."
        )
    elif state == "confused":
        return (
            "[SILENCE ALERT — CONFUSED] The user hesitated noticeably while typing. "
            "They may be unsure how to explain their issue. Ask exactly ONE clear, "
            "simple clarifying question before proceeding. Keep it brief."
        )
    return None  # confident = no intervention needed
