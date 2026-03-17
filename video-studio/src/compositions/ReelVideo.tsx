import React from "react";
import {
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
  spring,
  Img,
  Sequence,
} from "remotion";

interface Scene {
  text: string;
  imageUrl: string;
  duration: number;
}

interface Props {
  scenes: Scene[];
  brandName: string;
  accentColor: string;
}

export const ReelVideo: React.FC<Props> = ({ scenes, brandName, accentColor }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Calculate which scene we're in
  let currentScene = 0;
  let frameInScene = frame;
  let totalFrames = 0;
  for (let i = 0; i < scenes.length; i++) {
    if (frame >= totalFrames && frame < totalFrames + scenes[i].duration) {
      currentScene = i;
      frameInScene = frame - totalFrames;
      break;
    }
    totalFrames += scenes[i].duration;
  }

  const scene = scenes[currentScene] || scenes[0];

  // Scene transition
  const sceneOpacity = interpolate(frameInScene, [0, 10, scene.duration - 10, scene.duration], [0, 1, 1, 0], { extrapolateRight: "clamp" });
  const textY = spring({ frame: frameInScene, fps, from: 60, to: 0, durationInFrames: 20 });
  const textOpacity = interpolate(frameInScene, [5, 20], [0, 1], { extrapolateRight: "clamp" });
  const zoom = interpolate(frameInScene, [0, scene.duration], [1, 1.15], { extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ backgroundColor: "#0a0a15" }}>
      {/* Scene Background */}
      <AbsoluteFill style={{ opacity: sceneOpacity }}>
        {scene.imageUrl ? (
          <Img
            src={scene.imageUrl}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
              transform: `scale(${zoom})`,
            }}
          />
        ) : (
          <AbsoluteFill
            style={{
              background: `linear-gradient(135deg, ${accentColor}33, #0a0a15)`,
            }}
          />
        )}
        {/* Overlay */}
        <AbsoluteFill
          style={{
            background: "linear-gradient(180deg, transparent 40%, rgba(0,0,0,0.8) 100%)",
          }}
        />
      </AbsoluteFill>

      {/* Scene Text */}
      <AbsoluteFill
        style={{
          justifyContent: "flex-end",
          padding: "0 60px 200px",
        }}
      >
        <div
          style={{
            fontSize: 52,
            fontWeight: 900,
            color: "#fff",
            opacity: textOpacity,
            transform: `translateY(${textY}px)`,
            textShadow: "0 4px 20px rgba(0,0,0,0.8)",
            lineHeight: 1.2,
          }}
        >
          {scene.text}
        </div>
      </AbsoluteFill>

      {/* Brand Watermark */}
      <div
        style={{
          position: "absolute",
          top: 60,
          left: 60,
          fontSize: 18,
          fontWeight: 800,
          color: accentColor,
          letterSpacing: 4,
          opacity: 0.6,
        }}
      >
        {brandName}
      </div>

      {/* Scene Indicator */}
      <div
        style={{
          position: "absolute",
          bottom: 100,
          left: 0,
          right: 0,
          display: "flex",
          justifyContent: "center",
          gap: 8,
        }}
      >
        {scenes.map((_, i) => (
          <div
            key={i}
            style={{
              width: i === currentScene ? 30 : 8,
              height: 4,
              borderRadius: 2,
              backgroundColor: i === currentScene ? accentColor : "rgba(255,255,255,0.3)",
              transition: "width 0.3s",
            }}
          />
        ))}
      </div>
    </AbsoluteFill>
  );
};
