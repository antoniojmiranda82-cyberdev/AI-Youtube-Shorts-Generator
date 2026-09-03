"""Platform packaging helpers for QST Shorts.

Converts ranked/rendered shorts into a review manifest with platform-specific
metadata for YouTube Shorts, Instagram Reels, and Facebook Reels.
"""
from __future__ import annotations

import re
from typing import Dict, Iterable, List


def _clean_text(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _slug(value: str, max_len: int = 56) -> str:
    value = _clean_text(value).lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value[:max_len].rstrip("-") or "short"


def _hashtags(title: str, hook: str, limit: int = 5) -> List[str]:
    text = f"{title} {hook}".lower()
    tags: List[str] = []
    if any(word in text for word in ("theo", "podcast", "guest")):
        tags.extend(["#Podcast", "#Comedy"])
    if any(word in text for word in ("funny", "laugh", "crazy", "wild", "insane")):
        tags.append("#Funny")
    tags.extend(["#Shorts", "#Reels"])
    out: List[str] = []
    for tag in tags:
        if tag not in out:
            out.append(tag)
    return out[:limit]


def build_platform_metadata(short: Dict, index: int = 1) -> Dict:
    title = _clean_text(short.get("title") or short.get("hook_sentence") or f"Clip {index}")
    hook = _clean_text(short.get("hook_sentence") or title)
    score = short.get("qst_score", short.get("score"))
    tags = _hashtags(title, hook)
    stem = f"{index:02d}-{_slug(title)}"

    yt_title = title[:90]
    if "#Shorts" not in yt_title:
        yt_title = f"{yt_title} #Shorts"[:100]

    ig_caption = f"{hook}\n\n{' '.join(tags)}".strip()
    fb_caption = f"{hook}\n\n{' '.join(tag for tag in tags if tag != '#Shorts')}".strip()

    return {
        "index": index,
        "filename": f"{stem}.mp4",
        "review": {
            "score": score,
            "start_time": short.get("start_time"),
            "end_time": short.get("end_time"),
            "virality_reason": _clean_text(short.get("virality_reason")),
        },
        "youtube": {
            "title": yt_title,
            "description": f"{hook}\n\n{' '.join(tags)}".strip(),
        },
        "instagram": {
            "caption": ig_caption,
        },
        "facebook": {
            "caption": fb_caption,
        },
    }


def build_publishing_manifest(shorts: Iterable[Dict]) -> Dict:
    items = [build_platform_metadata(short, index=i) for i, short in enumerate(shorts, 1)]
    return {
        "version": 1,
        "platforms": ["youtube_shorts", "instagram_reels", "facebook_reels"],
        "items": items,
    }
