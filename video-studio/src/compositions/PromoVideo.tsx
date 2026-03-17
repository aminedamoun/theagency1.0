import React from "react";
import {
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
  spring,
  Sequence,
} from "remotion";

interface Props {
  title: string;
  subtitle: string;
  scenes: { text: string; icon: string }[];
  bgColor: string;
  accentColor: string;
}

export const PromoVideo: React.FC<Props> = ({
  title,
  subtitle,
  scenes,
  bgColor,
  accentColor,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const logoScale = spring({ frame, fps, from: 0, to: 1, durationInFrames: 25 });
  const titleOpacity = interpolate(frame, [15, 35], [0, 1], { extrapolateRight: "clamp" });
  const lineW = interpolate(frame, [25, 50], [0, 400], { extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ backgroundColor: bgColor }}>
      {/* Animated gradient background */}
      <div
        style={{
          position: "absolute",
          top: -200,
          right: -200,
          width: 600,
          height: 600,
          borderRadius: "50%",
          background: `radial-gradient(circle, ${accentColor}20, transparent 70%)`,
          transform: `scale(${interpolate(frame, [0, 450], [1, 1.5])})`,
        }}
      />

      {/* Intro (frames 0-120) */}
      <Sequence from={0} durationInFrames={120}>
        <AbsoluteFill
          style={{
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
            alignItems: "center",
          }}
        >
          <div
            style={{
              fontSize: 80,
              fontWeight: 900,
              color: accentColor,
              transform: `scale(${logoScale})`,
              letterSpacing: 8,
            }}
          >
            {title}
          </div>
          <div
            style={{
              width: lineW,
              height: 3,
              backgroundColor: accentColor,
              margin: "20px 0",
            }}
          />
          <div
            style={{
              fontSize: 28,
              color: "rgba(255,255,255,0.6)",
              opacity: titleOpacity,
              letterSpacing: 6,
              textTransform: "uppercase",
            }}
          >
            {subtitle}
          </div>
        </AbsoluteFill>
      </Sequence>

      {/* Service Scenes (frames 120+) */}
      {(scenes.length > 0 ? scenes : [
        { text: "Social Media Management", icon: "📱" },
        { text: "Content Creation", icon: "✍️" },
        { text: "Video Production", icon: "🎬" },
        { text: "Brand Strategy", icon: "🎯" },
      ]).map((scene, i) => (
        <Sequence key={i} from={120 + i * 80} durationInFrames={80}>
          <AbsoluteFill
            style={{
              display: "flex",
              flexDirection: "column",
              justifyContent: "center",
              alignItems: "center",
            }}
          >
            <div style={{ fontSize: 80, marginBottom: 20 }}>{scene.icon}</div>
            <div
              style={{
                fontSize: 48,
                fontWeight: 800,
                color: "#fff",
                textAlign: "center",
                opacity: interpolate(
                  frame - (120 + i * 80),
                  [0, 15, 65, 80],
                  [0, 1, 1, 0],
                  { extrapolateRight: "clamp", extrapolateLeft: "clamp" }
                ),
              }}
            >
              {scene.text}
            </div>
          </AbsoluteFill>
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
