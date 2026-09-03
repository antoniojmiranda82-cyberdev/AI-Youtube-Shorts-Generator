from shorts_generator.remotion_export import build_remotion_props


def test_build_remotion_props_normalizes_timing():
    transcript = {
        "segments": [
            {"start": 10.0, "end": 11.0, "text": "first line"},
            {"start": 11.0, "end": 12.5, "text": "second line"},
            {"start": 20.0, "end": 21.0, "text": "outside"},
        ]
    }
    highlight = {
        "start_time": 10.0,
        "end_time": 15.0,
        "title": "Fallback title",
        "hook_sentence": "Theo said what",
    }

    props = build_remotion_props(highlight, transcript, "clip.mp4")

    assert props["videoSrc"] == "clip.mp4"
    assert props["hook"] == "THEO SAID WHAT"
    assert props["captions"][0]["startMs"] == 0
    assert props["captions"][1]["startMs"] == 1000
    assert len(props["captions"]) == 2
    assert props["punchIns"]


def test_short_clip_skips_punch_ins():
    transcript = {"segments": []}
    highlight = {"start_time": 0.0, "end_time": 2.0, "title": "Tiny", "hook_sentence": ""}

    props = build_remotion_props(highlight, transcript, "tiny.mp4")

    assert props["hook"] == "TINY"
    assert props["punchIns"] == []
