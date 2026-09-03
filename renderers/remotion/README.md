# QST Shorts Remotion Renderer

This renderer turns one ranked short candidate into a 1080x1920 composition for Facebook Reels, Instagram Reels, and YouTube Shorts.

## Input shape

Pass props matching `QSTShortProps`:

```json
{
  "videoSrc": "file-or-url-to-precut-clip.mp4",
  "hook": "HE REALLY SAID THAT 😭",
  "captions": [
    {
      "text": "caption text",
      "startMs": 0,
      "endMs": 900,
      "timestampMs": 0,
      "confidence": 0.99
    }
  ],
  "punchIns": [
    {"startMs": 900, "endMs": 1800, "scale": 1.08}
  ]
}
```

Captions intentionally use Remotion's `Caption` JSON type. Keep all timing relative to the start of the exported short, not the original long-form video.

## Design rules

- 1080x1920, 30fps.
- Hook stays near the top and away from platform chrome.
- Captions stay above the lower interaction controls and leave extra room on the right side.
- Punch-ins are subtle and frame-driven. Do not use CSS animations or transitions.
- No intro or logo animation before the hook.
- Keep the first spoken payoff moving immediately.

## Local preview

```bash
cd renderers/remotion
npm install
npm run studio
```

## Render

```bash
npx remotion render src/index.ts QSTShort out/qst-short.mp4 --props=props.json
```

The next integration step is for the Python pipeline to generate one props JSON file per selected clip, including normalized caption timings and optional punch-in cues.
