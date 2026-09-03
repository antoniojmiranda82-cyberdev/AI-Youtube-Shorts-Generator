import unittest

from shorts_generator.qst_scoring import comedy_score, rerank_highlights


class ComedyScoringTests(unittest.TestCase):
    def test_funny_compact_clip_beats_long_context_clip(self):
        candidates = [
            {
                "title": "Guest loses it at absurd punchline",
                "start_time": 10,
                "end_time": 34,
                "score": 74,
                "hook_sentence": "You did WHAT?!",
                "virality_reason": "Guest laughter after an absurd unexpected punchline.",
            },
            {
                "title": "Background explanation",
                "start_time": 50,
                "end_time": 150,
                "score": 88,
                "hook_sentence": "Here is some background information",
                "virality_reason": "A detailed explanation of the topic.",
            },
        ]

        ranked = rerank_highlights(candidates, profile="comedy")

        self.assertEqual(ranked[0]["title"], "Guest loses it at absurd punchline")
        self.assertGreater(ranked[0]["qst_score"], ranked[1]["qst_score"])
        self.assertEqual(ranked[0]["source_score"], 74)

    def test_general_profile_preserves_source_score_order(self):
        candidates = [
            {"title": "A", "score": 55},
            {"title": "B", "score": 92},
        ]

        ranked = rerank_highlights(candidates, profile="general")

        self.assertEqual([item["title"] for item in ranked], ["B", "A"])

    def test_short_empty_hook_is_penalized(self):
        with_hook = {
            "title": "Unexpected reaction",
            "start_time": 0,
            "end_time": 25,
            "score": 70,
            "hook_sentence": "You seriously did that?!",
            "virality_reason": "unexpected reaction",
        }
        without_hook = dict(with_hook, hook_sentence="")

        self.assertGreater(comedy_score(with_hook), comedy_score(without_hook))

    def test_unknown_profile_fails_fast(self):
        with self.assertRaises(ValueError):
            rerank_highlights([], profile="not-a-profile")


if __name__ == "__main__":
    unittest.main()
