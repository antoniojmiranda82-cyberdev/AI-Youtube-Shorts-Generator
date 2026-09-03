import unittest

from shorts_generator.publishing import build_platform_metadata, build_publishing_manifest


class PublishingTests(unittest.TestCase):
    def test_builds_platform_copy_and_filename(self):
        short = {
            "title": "Theo realizes this dude is insane",
            "hook_sentence": "HE RAN 395 MILES WITHOUT SLEEP",
            "qst_score": 94,
            "start_time": 10.0,
            "end_time": 38.0,
            "virality_reason": "Immediate absurd premise and strong reaction.",
        }
        item = build_platform_metadata(short, 1)
        self.assertTrue(item["filename"].startswith("01-theo-realizes"))
        self.assertIn("#Shorts", item["youtube"]["title"])
        self.assertIn("HE RAN 395 MILES", item["instagram"]["caption"])
        self.assertEqual(item["review"]["score"], 94)

    def test_manifest_contains_all_three_platforms(self):
        manifest = build_publishing_manifest([{"title": "Funny clip"}])
        self.assertEqual(len(manifest["items"]), 1)
        self.assertIn("youtube_shorts", manifest["platforms"])
        self.assertIn("instagram_reels", manifest["platforms"])
        self.assertIn("facebook_reels", manifest["platforms"])


if __name__ == "__main__":
    unittest.main()
