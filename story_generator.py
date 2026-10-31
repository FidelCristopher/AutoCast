import os
import subprocess
import shutil
from pathlib import Path
from google import genai

STORY_PROMPT_TEMPLATE = """
You are a professional children's storyteller and educational content developer.
Your task is to write a structured, highly engaging children's story script in Indonesian. The script must be optimized for generating dynamic conversational explainer videos.

STORY THEME: {theme}
SPECIAL INSTRUCTIONS: {custom_prompt}
TARGET DURATION: Approximately 3-5 minutes narration

WRITING GUIDELINES:
1. TITLE: Catchy, warm, child-friendly (e.g. "Petualangan Kancil dan Kompas Pelangi").
2. YOUTUBE DESCRIPTION & TAGS: 2-3 engaging sentences + relevant hashtags (#CeritaAnak #DongengSebelumTidur #AnimasiEdukasi).
3. NARRATIVE SCRIPT:
   - Provide an immersive story script with rich sensory details, lively dialogue, and natural flow.
   - Use warm opening lines: "Hai teman-teman pintar! Pernah kepikiran gak, gimana kalau..."
   - Include 4 distinct acts:
     * Act 1: Character introduction & the initial quest/problem.
     * Act 2: Journey and fun obstacles.
     * Act 3: Creative discovery and teamwork.
     * Act 4: Heartwarming moral takeaway and closing remarks.
   - Write comprehensively (600 - 900 words) so the generated media output has sufficient depth.

OUTPUT FORMAT:
Provide the output strictly using the following delimiters:
===TITLE===
[Story Title Here]

===DESCRIPTION===
[YouTube Video Description Here]

===TAGS===
[Comma-separated tags here]

===STORY_CONTENT===
[Full story text script here]
"""

class StoryGenerator:
    def __init__(self, engine_mode: str = "pi_agent", api_key: str = ""):
        """
        engine_mode:
          - "pi_agent": Uses your authenticated Pi subscription (Gemini 3.8 Flash via WezTerm / WSL bridge).
          - "api_key": Uses a standard Gemini API key via official google-genai SDK.
        """
        self.engine_mode = engine_mode
        self.api_key = api_key.strip()

    def generate_story(self, theme: str, custom_prompt: str = "") -> dict:
        prompt = STORY_PROMPT_TEMPLATE.format(
            theme=theme,
            custom_prompt=custom_prompt if custom_prompt else "Create a cheerful, moral-rich story suitable for toddlers and primary school children."
        )

        if self.engine_mode == "pi_agent":
            raw_text = self._generate_via_pi_agent(prompt)
        else:
            raw_text = self._generate_via_api_key(prompt)

        return self._parse_story(raw_text)

    def _generate_via_pi_agent(self, prompt: str) -> str:
        """
        Calls Pi with your signed-in Gemini 3.8 Flash subscription via terminal bridge.
        Supports native Linux execution or Windows -> WSL bridge transparently.
        """
        # Save prompt to temporary file to avoid command-line escaping issues
        temp_dir = Path(os.environ.get("TEMP", "/tmp"))
        prompt_file = temp_dir / "autocast_story_prompt.txt"
        with open(prompt_file, "w", encoding="utf-8") as f:
            f.write(prompt)

        # Determine command depending on runtime OS
        if os.name == "nt":
            # On Windows, bridge into WSL where Pi agent with Antigravity session is running
            # Convert Windows temp path to WSL path
            drive = prompt_file.drive.replace(":", "").lower()
            wsl_prompt_path = f"/mnt/{drive}/{prompt_file.as_posix()[3:]}"
            cmd = [
                "wsl.exe", "bash", "-lic",
                f"cat '{wsl_prompt_path}' | pi --provider antigravity --model gemini-3.8-flash -p"
            ]
        else:
            cmd = [
                "bash", "-lic",
                f"cat '{prompt_file}' | pi --provider antigravity --model gemini-3.8-flash -p"
            ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            err = e.stderr or e.stdout or str(e)
            raise RuntimeError(f"Pi Agent Gemini 3.8 Flash bridge error: {err}")

    def _generate_via_api_key(self, prompt: str) -> str:
        if not self.api_key:
            raise ValueError("Gemini API Key is empty. Please enter your API Key or select 'Pi Agent Bridge' mode.")
        client = genai.Client(api_key=self.api_key)
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt,
        )
        return response.text or ""

    def _parse_story(self, text: str) -> dict:
        result = {
            "title": "Kisah Petualangan Ceria",
            "description": "Cerita dongeng seru dan mendidik untuk anak.",
            "tags": "cerita anak, dongeng fabel, dongeng sebelum tidur, kartun edukasi",
            "content": text
        }

        if "===TITLE===" in text:
            parts = text.split("===TITLE===")[1]
            if "===DESCRIPTION===" in parts:
                title_part, desc_rem = parts.split("===DESCRIPTION===", 1)
                result["title"] = title_part.strip()

                if "===TAGS===" in desc_rem:
                    desc_part, tags_rem = desc_rem.split("===TAGS===", 1)
                    result["description"] = desc_part.strip()

                    if "===STORY_CONTENT===" in tags_rem:
                        tags_part, story_part = tags_rem.split("===STORY_CONTENT===", 1)
                        result["tags"] = tags_part.strip()
                        result["content"] = story_part.strip()
                    else:
                        result["tags"] = tags_rem.strip()
                elif "===STORY_CONTENT===" in desc_rem:
                    desc_part, story_part = desc_rem.split("===STORY_CONTENT===", 1)
                    result["description"] = desc_part.strip()
                    result["content"] = story_part.strip()

        return result
