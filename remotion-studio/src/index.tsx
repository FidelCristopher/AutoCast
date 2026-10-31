import React from "react";
import { Composition, registerRoot } from "remotion";
import { StoryVideo, StoryVideoProps } from "./StoryVideo";

const defaultProps: StoryVideoProps = {
  title: "Petualangan Kancil dan Kompas Pelangi",
  scenes: [
    {
      imageSrc: "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=1280&q=80",
      caption: "Di sebuah hutan yang penuh warna, hiduplah seekor Kancil yang cerdik bernama Bobi.",
      durationInFrames: 90, // 3 detik @ 30fps
    },
    {
      imageSrc: "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=1280&q=80",
      caption: "Suatu hari, Bobi menemukan sebuah peta bercahaya di dekat pohon raksasa!",
      durationInFrames: 90,
    },
  ],
};

export const RemotionRoot: React.FC = () => {
  // Hitung total durasi dari semua scene
  const totalFrames = defaultProps.scenes.reduce(
    (acc, scene) => acc + scene.durationInFrames,
    0
  );

  return (
    <>
      {/* 16:9 Landscape YouTube Video */}
      <Composition
        id="StoryVideo"
        component={StoryVideo}
        durationInFrames={totalFrames || 180}
        fps={30}
        width={1280}
        height={720}
        defaultProps={defaultProps}
      />

      {/* 9:16 Vertical Video (YouTube Shorts & TikTok) */}
      <Composition
        id="StoryShorts"
        component={StoryVideo}
        durationInFrames={totalFrames || 180}
        fps={30}
        width={720}
        height={1280}
        defaultProps={defaultProps}
      />
    </>
  );
};

registerRoot(RemotionRoot);
