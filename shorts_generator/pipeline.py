"""End-to-end orchestrator.

Two modes:
  * mode="api"   (default) — MuAPI does download / transcribe / LLM / autocrop.
                              Fast, no local deps, pay-per-call.
  * mode="local"            — yt-dlp + faster-whisper + OpenAI or Gemini + ffmpeg/opencv.
                              Self-hosted, LLM_PROVIDER selects OpenAI or Gemini.
"""
from typing import Dict, List, Optional

from .clipper import crop_highlights
from .downloader import download_youtube
from .highlights import call_muapi_llm, get_highlights
from .publishing import build_publishing_manifest
from .qst_scoring import rerank_highlights
from .remotion_export import build_remotion_props
from .transcriber import transcribe


def _attach_render_props(shorts: List[Dict], transcript: Dict) -> List[Dict]:
    enriched: List[Dict] = []
    for short in shorts:
        item = dict(short)
        video_src = item.get("clip_url") or item.get("clip_path") or item.get("path") or ""
        if video_src and item.get("start_time") is not None and item.get("end_time") is not None:
            item["remotion_props"] = build_remotion_props(item, transcript, video_src)
        enriched.append(item)
    return enriched


def _build_result(
    mode: str,
    source_video_url: str,
    transcript: Dict,
    highlights: List[Dict],
    shorts: List[Dict],
    viral_profile: Optional[str],
) -> Dict:
    return {
        "mode": mode,
        "source_video_url": source_video_url,
        "transcript": transcript,
        "highlights": highlights,
        "shorts": shorts,
        "viral_profile": viral_profile,
        "publishing_manifest": build_publishing_manifest(shorts),
    }


def _run_local(
    youtube_url: str,
    num_clips: int,
    aspect_ratio: str,
    download_format: str,
    language: Optional[str],
    viral_profile: Optional[str],
) -> Dict:
    from .local.clipper import crop_highlights_local
    from .local.downloader import download_youtube_local
    from .local.llm import call_local_llm
    from .local.transcriber import transcribe_local

    source_path = download_youtube_local(youtube_url, fmt=download_format)
    transcript = transcribe_local(source_path, language=language)
    if not transcript["segments"]:
        raise RuntimeError("Whisper produced no segments. The video may have no detectable speech.")

    candidate_count = max(num_clips * 2, num_clips) if viral_profile else num_clips
    highlights_result = get_highlights(transcript, num_clips=candidate_count, llm_fn=call_local_llm)
    all_highlights: List[Dict] = highlights_result.get("highlights", [])
    if not all_highlights:
        raise RuntimeError("Highlight generator returned zero clips.")

    if viral_profile:
        all_highlights = rerank_highlights(all_highlights, transcript, viral_profile)

    top = sorted(all_highlights, key=lambda h: int(h.get("qst_score", h.get("score", 0))), reverse=True)[:num_clips]
    print(f"[pipeline/local] cropping {len(top)} of {len(all_highlights)} candidates", flush=True)
    shorts = _attach_render_props(crop_highlights_local(source_path, top, aspect_ratio=aspect_ratio), transcript)
    return _build_result("local", source_path, transcript, all_highlights, shorts, viral_profile)


def _run_api(
    youtube_url: str,
    num_clips: int,
    aspect_ratio: str,
    download_format: str,
    language: Optional[str],
    viral_profile: Optional[str],
) -> Dict:
    source_url = download_youtube(youtube_url, fmt=download_format)
    transcript = transcribe(source_url, language=language)
    if not transcript["segments"]:
        raise RuntimeError("Whisper produced no segments. The video may have no detectable speech.")

    candidate_count = max(num_clips * 2, num_clips) if viral_profile else num_clips
    highlights_result = get_highlights(transcript, num_clips=candidate_count, llm_fn=call_muapi_llm)
    all_highlights: List[Dict] = highlights_result.get("highlights", [])
    if not all_highlights:
        raise RuntimeError("Highlight generator returned zero clips.")

    if viral_profile:
        all_highlights = rerank_highlights(all_highlights, transcript, viral_profile)

    top = sorted(all_highlights, key=lambda h: int(h.get("qst_score", h.get("score", 0))), reverse=True)[:num_clips]
    print(f"[pipeline] cropping {len(top)} of {len(all_highlights)} candidates", flush=True)
    shorts = _attach_render_props(crop_highlights(source_url, top, aspect_ratio=aspect_ratio), transcript)
    return _build_result("api", source_url, transcript, all_highlights, shorts, viral_profile)


def generate_shorts(
    youtube_url: str,
    num_clips: int = 3,
    aspect_ratio: str = "9:16",
    download_format: str = "720",
    language: Optional[str] = None,
    mode: str = "api",
    viral_profile: Optional[str] = None,
) -> Dict:
    """Run the full pipeline and return a structured result."""
    mode = (mode or "api").lower()
    if mode == "local":
        return _run_local(youtube_url, num_clips, aspect_ratio, download_format, language, viral_profile)
    if mode == "api":
        return _run_api(youtube_url, num_clips, aspect_ratio, download_format, language, viral_profile)
    raise ValueError(f"Unknown mode: {mode!r}. Use 'api' or 'local'.")
