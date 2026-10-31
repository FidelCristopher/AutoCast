import os
import json
import subprocess
from pathlib import Path

REMOTION_STUDIO_DIR = Path(__file__).resolve().parent / "remotion-studio"

class RemotionVideoEngine:
    def __init__(self, studio_dir: Path = REMOTION_STUDIO_DIR):
        self.studio_dir = Path(studio_dir)
        self.cli_entry = self.studio_dir / "node_modules" / "@remotion" / "cli" / "remotion-cli.js"

    def render_story_video(
        self,
        composition_id: str, # "StoryVideo" (16:9) or "StoryShorts" (9:16)
        title: str,
        scenes: list,
        output_mp4_path: str,
        audio_src: str = None,
        status_callback=None
    ) -> str:
        """
        Renders a dynamic motion graphic story video via Remotion.
        Each scene dict: {"imageSrc": str, "caption": str, "durationInFrames": int}
        """
        out_path = Path(output_mp4_path).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)

        props = {
            "title": title,
            "scenes": scenes
        }
        if audio_src:
            props["audioSrc"] = audio_src

        props_json_str = json.dumps(props)

        if status_callback:
            status_callback(f"Starting Remotion render for [{composition_id}]...")

        # Run via node directly on Windows or cross-platform
        node_cmd = "node"
        entry_str = str(self.cli_entry).replace("\\", "/")
        out_str = str(out_path).replace("\\", "/")

        cmd = [
            node_cmd,
            str(self.cli_entry),
            "render",
            composition_id,
            str(out_path),
            f"--props={props_json_str}",
            "--concurrency=2"
        ]

        if status_callback:
            status_callback("Rendering frames with spring physics and camera motion...")

        process = subprocess.Popen(
            cmd,
            cwd=str(self.studio_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8"
        )

        for line in process.stdout:
            line_str = line.strip()
            if "Rendered" in line_str or "Encoded" in line_str:
                if status_callback:
                    status_callback(line_str)

        process.wait()

        if process.returncode != 0:
            raise RuntimeError(f"Remotion render failed with exit code {process.returncode}")

        if status_callback:
            status_callback(f"Render complete: {out_path.name}")

        return str(out_path)
