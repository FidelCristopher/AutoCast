import React from "react";
import {
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
  Img,
  Audio,
  staticFile,
  spring,
} from "remotion";

export interface Scene {
  imageSrc: string;
  caption: string;
  durationInFrames: number;
}

export interface StoryVideoProps {
  title: string;
  audioSrc?: string;
  scenes: Scene[];
}

export const StoryVideo: React.FC<StoryVideoProps> = ({
  title,
  audioSrc,
  scenes,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Hitung scene mana yang sedang aktif berdasarkan timeline frame
  let accumulatedFrames = 0;
  let activeSceneIndex = 0;
  let sceneStartFrame = 0;

  for (let i = 0; i < scenes.length; i++) {
    const dur = scenes[i].durationInFrames;
    if (frame >= accumulatedFrames && frame < accumulatedFrames + dur) {
      activeSceneIndex = i;
      sceneStartFrame = accumulatedFrames;
      break;
    }
    accumulatedFrames += dur;
  }

  const currentScene = scenes[activeSceneIndex] || scenes[0];
  const sceneProgressFrame = frame - sceneStartFrame;
  const sceneDuration = currentScene.durationInFrames;

  // Efek Kamera Bergerak Halus (Ken Burns Effect: Zoom In & Slight Pan)
  const scale = interpolate(
    sceneProgressFrame,
    [0, sceneDuration],
    [1.0, 1.15],
    { extrapolateRight: "clamp" }
  );

  const translateY = interpolate(
    sceneProgressFrame,
    [0, sceneDuration],
    [0, -15],
    { extrapolateRight: "clamp" }
  );

  // Animasi Pop-In untuk Teks Caption
  const textSpring = spring({
    frame: sceneProgressFrame,
    fps,
    config: {
      damping: 12,
      stiffness: 120,
    },
  });

  return (
    <AbsoluteFill style={{ backgroundColor: "#0f172a" }}>
      {/* Background Image Layer with Dynamic Ken Burns Camera */}
      <AbsoluteFill
        style={{
          overflow: "hidden",
          transform: `scale(${scale}) translateY(${translateY}px)`,
          transformOrigin: "center center",
        }}
      >
        <Img
          src={currentScene.imageSrc}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
          }}
        />
      </AbsoluteFill>

      {/* Cinematic Vignette Overlay */}
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(circle, transparent 55%, rgba(0, 0, 0, 0.7) 100%)",
        }}
      />

      {/* Title Card at the top */}
      <div
        style={{
          position: "absolute",
          top: 40,
          left: 40,
          right: 40,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <div
          style={{
            backgroundColor: "rgba(15, 23, 42, 0.8)",
            padding: "10px 24px",
            borderRadius: 30,
            border: "1px solid rgba(255, 255, 255, 0.2)",
            color: "#ffffff",
            fontFamily: "system-ui, sans-serif",
            fontSize: 22,
            fontWeight: "bold",
            letterSpacing: 0.5,
          }}
        >
          {title}
        </div>
      </div>

      {/* Dynamic Animated Subtitle / Story Caption at Bottom */}
      <div
        style={{
          position: "absolute",
          bottom: 60,
          left: 60,
          right: 60,
          display: "flex",
          justifyContent: "center",
        }}
      >
        <div
          style={{
            backgroundColor: "rgba(0, 0, 0, 0.75)",
            backdropFilter: "blur(8px)",
            padding: "20px 36px",
            borderRadius: 24,
            border: "2px solid #38bdf8",
            color: "#ffffff",
            fontFamily: "Comic Sans MS, system-ui, cursive, sans-serif",
            fontSize: 32,
            fontWeight: 800,
            textAlign: "center",
            lineHeight: 1.4,
            transform: `scale(${textSpring})`,
            boxShadow: "0 10px 30px rgba(0,0,0,0.5)",
            maxWidth: "85%",
          }}
        >
          {currentScene.caption}
        </div>
      </div>

      {/* Optional Narration Audio */}
      {audioSrc && <Audio src={audioSrc} />}
    </AbsoluteFill>
  );
};
