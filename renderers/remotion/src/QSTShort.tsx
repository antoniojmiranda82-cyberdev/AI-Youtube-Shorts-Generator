import React from 'react';
import type {Caption} from '@remotion/captions';
import {Video} from '@remotion/media';
import {AbsoluteFill, Easing, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';

export type PunchIn = {
  startMs: number;
  endMs: number;
  scale?: number;
};

export type QSTShortProps = {
  videoSrc: string;
  hook: string;
  captions: Caption[];
  punchIns?: PunchIn[];
};

const getActiveCaption = (captions: Caption[], timeMs: number) =>
  captions.find((caption) => timeMs >= caption.startMs && timeMs < caption.endMs);

const getPunchScale = (punchIns: PunchIn[], timeMs: number) => {
  const active = punchIns.find((cue) => timeMs >= cue.startMs && timeMs <= cue.endMs);
  if (!active) return 1;
  const mid = (active.startMs + active.endMs) / 2;
  const target = active.scale ?? 1.08;
  if (timeMs <= mid) {
    return interpolate(timeMs, [active.startMs, mid], [1, target], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
      easing: Easing.bezier(0.16, 1, 0.3, 1),
    });
  }
  return interpolate(timeMs, [mid, active.endMs], [target, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });
};

export const QSTShort: React.FC<QSTShortProps> = ({videoSrc, hook, captions, punchIns = []}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const timeMs = (frame / fps) * 1000;
  const caption = getActiveCaption(captions, timeMs);
  const scale = getPunchScale(punchIns, timeMs);

  return (
    <AbsoluteFill style={{backgroundColor: '#050505', overflow: 'hidden'}}>
      <Video
        src={videoSrc}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          objectPosition: 'center center',
          scale,
        }}
      />

      <AbsoluteFill
        style={{
          pointerEvents: 'none',
          background: 'linear-gradient(180deg, rgba(0,0,0,0.52) 0%, rgba(0,0,0,0.02) 28%, rgba(0,0,0,0.02) 64%, rgba(0,0,0,0.58) 100%)',
        }}
      />

      <div
        style={{
          position: 'absolute',
          top: 118,
          left: 74,
          right: 74,
          textAlign: 'center',
          fontFamily: 'Arial, Helvetica, sans-serif',
          fontWeight: 900,
          fontSize: 70,
          lineHeight: 1.02,
          letterSpacing: -2,
          color: 'white',
          textShadow: '0 4px 18px rgba(0,0,0,0.85)',
        }}
      >
        {hook}
      </div>

      {caption ? (
        <div
          style={{
            position: 'absolute',
            left: 96,
            right: 150,
            bottom: 300,
            textAlign: 'center',
            fontFamily: 'Arial, Helvetica, sans-serif',
            fontWeight: 900,
            fontSize: 72,
            lineHeight: 1.05,
            letterSpacing: -1.5,
            color: 'white',
            WebkitTextStroke: '3px rgba(0,0,0,0.85)',
            paintOrder: 'stroke fill',
            textShadow: '0 5px 16px rgba(0,0,0,0.8)',
          }}
        >
          {caption.text.trim()}
        </div>
      ) : null}
    </AbsoluteFill>
  );
};
