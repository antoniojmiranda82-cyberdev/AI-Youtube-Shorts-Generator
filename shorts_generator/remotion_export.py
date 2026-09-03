"""Build Remotion-ready props from a ranked highlight and Whisper transcript."""
from typing import Dict, List


def _caption_segments(transcript: Dict, start: float, end: float) -> List[Dict]:
    captions: List[Dict] = []
    for segment in transcript.get("segments", []):
        seg_start = float(segment.get("start", 0.0))
        seg_end = float(segment.get("end", seg_start))
        if seg_end <= start or seg_start >= end:
            continue

        local_start = max(seg_start, start) - start
        local_end = min(seg_end, end) - start
        text = str(segment.get("text") or "").strip()
        if not text or local_end <= local_start:
            continue

        captions.append(
            {
                "text": text,
                "startMs": round(local_start * 1000),
                "endMs": round(local_end * 1000),
                "timestampMs": round(local_start * 1000),
                "confidence": None,
            }
        )
    return captions


def _default_punch_ins(highlight: Dict) -> List[Dict]:
    duration_ms = max(0, round((float(highlight["end_time"]) - float(highlight["start_time"])) * 1000))
    if duration_ms < 2500:
        return []

    cues = [{"startMs": 650, "endMs": min(1650, duration_ms - 1), "scale": 1.06}]
    if duration_ms >= 9000:
        payoff_start = max(2500, duration_ms - 3200)
        cues.append({"startMs": payoff_start, "endMs": min(duration_ms - 1, payoff_start + 1400), "scale": 1.08})
    return cues


def build_remotion_props(highlight: Dict, transcript: Dict, video_src: str) -> Dict:
    """Convert one selected highlight into the renderer's JSON contract."""
    start = float(highlight["start_time"])
    end = float(highlight["end_time"])
    hook = str(highlight.get("hook_sentence") or highlight.get("title") or "WAIT FOR IT").strip()

    return {
        "videoSrc": video_src,
        "hook": hook.upper(),
        "captions": _caption_segments(transcript, start, end),
        "punchIns": _default_punch_ins(highlight),
    }
