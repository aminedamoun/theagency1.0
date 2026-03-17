import React from "react";
import {
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
  spring,
  Video,
  Sequence,
} from "remotion";

interface Subtitle {
  text: string;
  start: number;
  end: number;
}

interface Props {
  videoUrl: string;
  subtitles: Subtitle[];
  style: "bold" | "minimal" | "karaoke" | "subtitle";
}

export const SubtitleVideo: React.FC<Props> = ({ videoUrl, subtitles, style }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Find current subtitle
  const currentSub = subtitles.find((s) => frame >= s.start && frame < s.end);

  const getSubtitleStyle = (): React.CSSProperties => {
    const base: React.CSSProperties = {
      position: "absolute",
      bottom: 120,
      left: 40,
      right: 40,
      textAlign: "center",
    };

    switch (style) {
      case "bold":
        return {
          ...base,
          fontSize: 48,
          fontWeight: 900,
          color: "#fff",
          textShadow: "0 4px 12px rgba(0,0,0,0.8), 0 0 40px rgba(0,0,0,0.4)",
          textTransform: "uppercase",
        };
      case "minimal":
        return {
          ...base,
          fontSize: 32,
          fontWeight: 500,
          color: "#fff",
          backgroundColor: "rgba(0,0,0,0.6)",
          padding: "8px 20px",
          borderRadius: 8,
          display: "inline-block",
        };
      case "karaoke":
        return {
          ...base,
          fontSize: 42,
          fontWeight: 800,
          color: "#c9a84c",
          textShadow: "0 2px 8px rgba(0,0,0,0.8)",
        };
      case "subtitle":
      default:
        return {
          ...base,
          bottom: 60,
          fontSize: 28,
          fontWeight: 400,
          color: "#fff",
          backgroundColor: "rgba(0,0,0,0.75)",
          padding: "6px 16px",
          borderRadius: 4,
        };
    }
  };

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {/* Video Background */}
      {videoUrl ? (
        <Video src={videoUrl} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      ) : (
        <AbsoluteFill
          style={{
            background: "linear-gradient(180deg, #1a1a2e 0%, #0a0a15 100%)",
          }}
        />
      )}

      {/* Subtitle */}
      {currentSub && (
        <div style={getSubtitleStyle()}>
          {style === "karaoke" ? (
            // Word-by-word highlight
            currentSub.text.split(" ").map((word, i) => {
              const wordFrame = currentSub.start + (i * (currentSub.end - currentSub.start)) / currentSub.text.split(" ").length;
              const isActive = frame >= wordFrame;
              return (
                <span
                  key={i}
                  style={{
                    color: isActive ? "#c9a84c" : "rgba(255,255,255,0.4)",
                    transition: "color 0.2s",
                    marginRight: 8,
                  }}
                >
                  {word}
                </span>
              );
            })
          ) : (
            <span
              style={{
                opacity: interpolate(
                  frame,
                  [currentSub.start, currentSub.start + 5, currentSub.end - 5, currentSub.end],
                  [0, 1, 1, 0],
                  { extrapolateRight: "clamp", extrapolateLeft: "clamp" }
                ),
              }}
            >
              {currentSub.text}
            </span>
          )}
        </div>
      )}
    </AbsoluteFill>
  );
};
