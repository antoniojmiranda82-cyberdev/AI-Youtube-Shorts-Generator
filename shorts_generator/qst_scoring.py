"""QST-specific reranking for short-form clip candidates.

The upstream highlight model is intentionally general-purpose. This module adds
an inexpensive deterministic second pass so comedy/podcast clips favor fast
hooks, compact payoff arcs, and reaction-heavy moments before rendering.
"""

import re
from typing import Dict, List


COMEDY_TERMS = {
    "laugh": 5,
    "laughter": 7,
    "funny": 5,
    "joke": 5,
    "absurd": 6,
    "ridiculous": 6,
    "wild": 4,
    "crazy": 4,
    "weird": 4,
    "unexpected": 5,
    "reaction": 5,
    "roast": 7,
    "deadpan": 7,
    "confession": 4,
    "surprise": 4,
    "shocked": 5,
    "disbelief": 5,
    "punchline": 8,
}

SLOW_CONTEXT_TERMS = {
    "introduction": -8,
    "sponsor": -12,
    "housekeeping": -10,
    "background": -3,
    "explains": -2,
    "explanation": -2,
}


def _text(candidate: Dict) -> str:
    return " ".join(
        str(candidate.get(key) or "")
        for key in ("title", "hook_sentence", "virality_reason")
    ).lower()


def _duration_score(seconds: float) -> int:
    """Prefer compact comedy clips, while allowing slightly longer story arcs."""
    if 15 <= seconds <= 35:
        return 10
    if 35 < seconds <= 45:
        return 7
    if 10 <= seconds < 15:
        return 4
    if 45 < seconds <= 60:
        return 2
    if seconds < 8:
        return -5
    if seconds > 90:
        return -12
    if seconds > 60:
        return -5
    return 0


def _hook_score(hook: str) -> int:
    hook = (hook or "").strip()
    if not hook:
        return -8

    words = re.findall(r"\b\w+\b", hook)
    score = 0
    if 3 <= len(words) <= 14:
        score += 5
    elif len(words) > 24:
        score -= 4

    if "?" in hook or "!" in hook:
        score += 2
    if any(token in hook.lower() for token in ("i ", "you ", "this ", "that ", "why ", "how ")):
        score += 2
    return score


def comedy_score(candidate: Dict) -> int:
    """Return a 0-100 comedy-first score derived from the model candidate."""
    base = int(candidate.get("score", 0) or 0)
    start = float(candidate.get("start_time", 0) or 0)
    end = float(candidate.get("end_time", start) or start)
    duration = max(0.0, end - start)
    text = _text(candidate)

    score = base + _duration_score(duration) + _hook_score(candidate.get("hook_sentence", ""))

    for term, weight in COMEDY_TERMS.items():
        if term in text:
            score += weight

    for term, weight in SLOW_CONTEXT_TERMS.items():
        if term in text:
            score += weight

    # Reward language suggesting a complete comic arc rather than a loose quote.
    if any(term in text for term in ("payoff", "escalat", "standalone", "self-contained")):
        score += 4

    return max(0, min(100, score))


def rerank_highlights(highlights: List[Dict], profile: str = "general") -> List[Dict]:
    """Return candidates sorted for the requested publishing goal."""
    profile = (profile or "general").strip().lower()
    if profile == "general":
        return sorted(highlights, key=lambda h: int(h.get("score", 0) or 0), reverse=True)
    if profile != "comedy":
        raise ValueError("Unknown viral profile. Use 'general' or 'comedy'.")

    ranked: List[Dict] = []
    for candidate in highlights:
        item = dict(candidate)
        item["source_score"] = int(candidate.get("score", 0) or 0)
        item["qst_score"] = comedy_score(candidate)
        item["score"] = item["qst_score"]
        ranked.append(item)

    ranked.sort(key=lambda h: int(h.get("qst_score", 0)), reverse=True)
    return ranked
