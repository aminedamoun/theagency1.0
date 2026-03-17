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

interface Props {
  headline: string;
  subtext: string;
  ctaText: string;
  bgColor: string;
  accentColor: string;
  bgImageUrl: string;
  logoUrl: string;
}

export const SocialMediaPost: React.FC<Props> = ({
  headline,
  subtext,
  ctaText,
  bgColor,
  accentColor,
  bgImageUrl,
  logoUrl,
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  // Animations
  const titleScale = spring({ frame, fps, from: 0, to: 1, durationInFrames: 30 });
  const titleOpacity = interpolate(frame, [0, 15], [0, 1], { extrapolateRight: "clamp" });
  const subtextOpacity = interpolate(frame, [20, 40], [0, 1], { extrapolateRight: "clamp" });
  const subtextY = interpolate(frame, [20, 40], [30, 0], { extrapolateRight: "clamp" });
  const ctaOpacity = interpolate(frame, [40, 60], [0, 1], { extrapolateRight: "clamp" });
  const lineWidth = interpolate(frame, [30, 50], [0, 300], { extrapolateRight: "clamp" });
  const bgZoom = interpolate(frame, [0, 150], [1, 1.08], { extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ backgroundColor: bgColor }}>
      {/* Background Image */}
      {bgImageUrl && (
        <AbsoluteFill style={{ transform: `scale(${bgZoom})` }}>
          <Img src={bgImageUrl} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
          <div style={{ position: "absolute", inset: 0, background: "rgba(0,0,0,0.4)" }} />
        </AbsoluteFill>
      )}

      {/* Content */}
      <AbsoluteFill
        style={{
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          padding: 80,
        }}
      >
        {/* Headline */}
        <div
          style={{
            fontSize: 72,
            fontWeight: 900,
            color: "#fff",
            textAlign: "center",
            transform: `scale(${titleScale})`,
            opacity: titleOpacity,
            textShadow: "0 4px 20px rgba(0,0,0,0.5)",
            lineHeight: 1.1,
          }}
        >
          {headline}
        </div>

        {/* Accent Line */}
        <div
          style={{
            width: lineWidth,
            height: 4,
            backgroundColor: accentColor,
            marginTop: 30,
            marginBottom: 30,
            borderRadius: 2,
          }}
        />

        {/* Subtext */}
        <div
          style={{
            fontSize: 32,
            color: "rgba(255,255,255,0.8)",
            textAlign: "center",
            opacity: subtextOpacity,
            transform: `translateY(${subtextY}px)`,
          }}
        >
          {subtext}
        </div>

        {/* CTA */}
        <Sequence from={45}>
          <div
            style={{
              marginTop: 50,
              padding: "16px 40px",
              backgroundColor: accentColor,
              borderRadius: 8,
              fontSize: 24,
              fontWeight: 700,
              color: "#000",
              opacity: ctaOpacity,
            }}
          >
            {ctaText}
          </div>
        </Sequence>
      </AbsoluteFill>

      {/* Logo */}
      {logoUrl && (
        <Img
          src={logoUrl}
          style={{
            position: "absolute",
            bottom: 40,
            right: 40,
            width: 80,
            height: 80,
            opacity: interpolate(frame, [50, 70], [0, 1], { extrapolateRight: "clamp" }),
          }}
        />
      )}
    </AbsoluteFill>
  );
};
