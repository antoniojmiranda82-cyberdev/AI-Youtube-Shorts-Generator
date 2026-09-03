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
from .qst_scoring import rerank_highlights
from .transcriber import transcribe


def _rank_candidates(highlights: List[Dict], viral_profile: str) -> List[Dict]:
    ranked = rerank_highlights(highlights, profile=viral_profile)
    if viral_profile != "general":
        print(
            f"[pipeline] applied viral profile={viral_profile!r} to {len(ranked)} candidates",
            flush=True,
        )
    return ranked


def _run_local(
    youtube_url: str,
    num_clips: int,
    aspect_ratio: str,
    download_format: str,
    language: Optional[str],
    viral_profile: str,
) -> Dict:
    from .local.clipper import crop_highlights_local
    from .local.downloader import download_youtube_local
    from .local.llm import call_local_llm
    from .local.transcriber import transcribe_local

    source_path = download_youtube_local(youtube_url, fmt=download_format)

    transcript = transcribe_local(source_path, language=language)
    if not transcript["segments"]:
        raise RuntimeError(
            "Whisper produced no segments. The video may have no detectable speech."
        )

    # Ask the upstream selector for extra candidates so the QST reranker has
    # enough headroom to find stronger comedy moments before rendering.
    candidate_target = max(num_clips * 3, num_clips)
    highlights_result = get_highlights(
        transcript,
        num_clips=candidate_target,
        llm_fn=call_local_llm,
    )
    all_highlights: List[Dict] = highlights_result.get("highlights", [])
    if not all_highlights:
        raise RuntimeError("Highlight generator returned zero clips.")

    ranked = _rank_candidates(all_highlights, viral_profile)
    top = ranked[:num_clips]
    print(f"[pipeline/local] cropping {len(top)} of {len(ranked)} ranked candidates", flush=True)

    shorts = crop_highlights_local(source_path, top, aspect_ratio=aspect_ratio)

    return {
        "mode": "local",
        "viral_profile": viral_profile,
        "source_video_url": source_path,
        "transcript": transcript,
        "highlights": ranked,
        "shorts": shorts,
    }


def _run_api(
    youtube_url: str,
    num_clips: int,
    aspect_ratio: str,
    download_format: str,
    language: Optional[str],
    viral_profile: str,
) -> Dict:
    source_url = download_youtube(youtube_url, fmt=download_format)

    transcript = transcribe(source_url, language=language)
    if not transcript["segments"]:
        raise RuntimeError(
            "Whisper produced no segments. The video may have no detectable speech."
        )

    candidate_target = max(num_clips * 3, num_clips)
    highlights_result = get_highlights(
        transcript,
        num_clips=candidate_target,
        llm_fn=call_muapi_llm,
    )
    all_highlights: List[Dict] = highlights_result.get("highlights", [])
    if not all_highlights:
        raise RuntimeError("Highlight generator returned zero clips.")

    ranked = _rank_candidates(all_highlights, viral_profile)
    top = ranked[:num_clips]
    print(f"[pipeline] cropping {len(top)} of {len(ranked)} ranked candidates", flush=True)

    shorts = crop_highlights(source_url, top, aspect_ratio=aspect_ratio)

    return {
        "mode": "api",
        "viral_profile": viral_profile,
        "source_video_url": source_url,
        "transcript": transcript,
        "highlights": ranked,
        "shorts": shorts,
    }


def generate_shorts(
    youtube_url: str,
    num_clips: int = 3,
    aspect_ratio: str = "9:16",
    download_format: str = "720",
    language: Optional[str] = None,
    mode: str = "api",
    viral_profile: str = "general",
) -> Dict:
    """Run the full pipeline and return a structured result.

    Args:
        youtube_url: source URL.
        num_clips: how many shorts to render.
        aspect_ratio: e.g. "9:16", "1:1".
        download_format: source resolution ("360" / "480" / "720" / "1080").
        language: ISO-639-1 to force Whisper language detection.
        mode: "api" (default, MuAPI) or "local" (yt-dlp + faster-whisper +
            OpenAI or Gemini + ffmpeg).
        viral_profile: ranking goal. "general" preserves upstream behavior;
            "comedy" favors fast hooks, reactions, and compact punchlines.

    Returns:
        {
          "mode": "api" | "local",
          "viral_profile": "general" | "comedy",
          "source_video_url": str,
          "transcript": {...},
          "highlights": [...],       # all candidates reranked
          "shorts": [...],           # top `num_clips` with clip_url / local path
        }
    """
    mode = (mode or "api").lower()
    viral_profile = (viral_profile or "general").lower()
    if viral_profile not in {"general", "comedy"}:
        raise ValueError("Unknown viral_profile. Use 'general' or 'comedy'.")

    if mode == "local":
        return _run_local(
            youtube_url,
            num_clips,
            aspect_ratio,
            download_format,
            language,
            viral_profile,
        )
    if mode == "api":
        return _run_api(
            youtube_url,
            num_clips,
            aspect_ratio,
            download_format,
            language,
            viral_profile,
        )
    raise ValueError(f"Unknown mode: {mode!r}. Use 'api' or 'local'.")
