import React from 'react';
import {Composition} from 'remotion';
import {QSTShort, type QSTShortProps} from './QSTShort';

const sampleProps: QSTShortProps = {
  videoSrc: 'https://remotion.media/video.mp4',
  hook: 'HE REALLY SAID THAT 😭',
  captions: [
    {text: 'Sample caption', startMs: 0, endMs: 1200, timestampMs: 0, confidence: 1},
  ],
  punchIns: [{startMs: 900, endMs: 1800, scale: 1.08}],
};

export const Root: React.FC = () => {
  return (
    <Composition
      id="QSTShort"
      component={QSTShort}
      durationInFrames={900}
      fps={30}
      width={1080}
      height={1920}
      defaultProps={sampleProps}
    />
  );
};
