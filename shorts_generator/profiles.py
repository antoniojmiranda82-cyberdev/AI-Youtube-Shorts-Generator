"""Highlight-selection profiles for different short-form goals."""

from typing import Dict


PROFILES: Dict[str, str] = {
    "general": "",
    "comedy": """
COMEDY / PODCAST BOOSTERS:
- Prefer moments that are funny without requiring outside context.
- Strongly reward an immediate absurd statement, unexpected comparison, confession, roast, or deadpan line.
- Strongly reward visible/audible guest laughter, surprise, disbelief, or a reaction that becomes part of the joke.
- Prefer setup -> escalation -> payoff arcs that complete in 15-45 seconds.
- Prefer quotable lines viewers will repeat in comments or send to friends.
- Penalize long explanations before the joke, sponsor reads, housekeeping, introductions, and clips that need more than ~3 seconds of context.
- Penalize clips where the funniest line occurs too late unless the escalation is unusually strong.
- When two clips are similarly funny, prefer the shorter and more self-contained one.
- A score above 90 should be reserved for a clip with a clear scroll-stopping opening AND a strong payoff/reaction.
""",
}


def get_profile_instructions(profile: str) -> str:
    """Return prompt instructions for a named highlight profile."""
    normalized = (profile or "general").strip().lower()
    if normalized not in PROFILES:
        raise ValueError(
            f"Unknown highlight profile: {profile!r}. "
            f"Use one of: {', '.join(sorted(PROFILES))}."
        )
    return PROFILES[normalized]
