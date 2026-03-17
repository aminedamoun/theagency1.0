import React from "react";
import { Composition } from "remotion";
import { SocialMediaPost } from "./compositions/SocialMediaPost";
import { ReelVideo } from "./compositions/ReelVideo";
import { PromoVideo } from "./compositions/PromoVideo";
import { SubtitleVideo } from "./compositions/SubtitleVideo";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      {/* Instagram Post with animations */}
      <Composition
        id="SocialMediaPost"
        component={SocialMediaPost}
        durationInFrames={150}
        fps={30}
        width={1080}
        height={1080}
        defaultProps={{
          headline: "YOUR HEADLINE HERE",
          subtext: "Subtext goes here",
          ctaText: "LEARN MORE →",
          bgColor: "#1a1a2e",
          accentColor: "#c9a84c",
          bgImageUrl: "",
          logoUrl: "",
        }}
      />

      {/* Reel / Story (9:16) */}
      <Composition
        id="ReelVideo"
        component={ReelVideo}
        durationInFrames={300}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{
          scenes: [
            { text: "Scene 1", imageUrl: "", duration: 90 },
            { text: "Scene 2", imageUrl: "", duration: 90 },
            { text: "Scene 3", imageUrl: "", duration: 90 },
          ],
          brandName: "DUBAI PROD",
          accentColor: "#c9a84c",
        }}
      />

      {/* Promo Video (16:9) */}
      <Composition
        id="PromoVideo"
        component={PromoVideo}
        durationInFrames={450}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          title: "DUBAI PROD",
          subtitle: "Social Media Agency",
          scenes: [],
          bgColor: "#0a0a15",
          accentColor: "#c9a84c",
        }}
      />

      {/* Video with Subtitles */}
      <Composition
        id="SubtitleVideo"
        component={SubtitleVideo}
        durationInFrames={300}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{
          videoUrl: "",
          subtitles: [
            { text: "Welcome to Dubai Prod", start: 0, end: 60 },
            { text: "We create amazing content", start: 60, end: 120 },
            { text: "Let's grow together", start: 120, end: 180 },
          ],
          style: "bold",
        }}
      />
    </>
  );
};
