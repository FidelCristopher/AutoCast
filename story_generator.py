import os
import json
import urllib.request
import subprocess
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
    def __init__(self, config: dict):
        self.config = config
        self.engine_mode = config.get("engine_mode", "pi_agent")

    def generate_story(self, theme: str, custom_prompt: str = "") -> dict:
        prompt = STORY_PROMPT_TEMPLATE.format(
            theme=theme,
            custom_prompt=custom_prompt if custom_prompt else "Create a cheerful, moral-rich story suitable for toddlers and primary school children."
        )

        if self.engine_mode == "pi_agent":
            raw_text = self._generate_via_cli_bridge(prompt)
        elif self.engine_mode == "openai_compatible":
            raw_text = self._generate_via_openai_endpoint(prompt)
        elif self.engine_mode == "manual":
            raw_text = prompt
            return {
                "title": f"Story Prompt: {theme}",
                "description": "Copy this prompt and paste it into your preferred web AI chat.",
                "tags": "cerita anak, dongeng fabel, edukasi",
                "content": prompt
            }
        else:
            raw_text = self._generate_via_gemini_api(prompt)

        return self._parse_story(raw_text)

    def _generate_via_cli_bridge(self, prompt: str) -> str:
        cli_cmd = self.config.get("cli_command", "pi --provider antigravity --model gemini-3.8-flash -p").strip()
        temp_dir = Path(os.environ.get("TEMP", "/tmp"))
        prompt_file = temp_dir / "autocast_story_prompt.txt"
        with open(prompt_file, "w", encoding="utf-8") as f:
            f.write(prompt)

        if os.name == "nt":
            drive = prompt_file.drive.replace(":", "").lower()
            wsl_prompt_path = f"/mnt/{drive}/{prompt_file.as_posix()[3:]}"
            cmd = [
                "wsl.exe", "bash", "-lic",
                f"cat '{wsl_prompt_path}' | {cli_cmd}"
            ]
        else:
            cmd = [
                "bash", "-lic",
                f"cat '{prompt_file}' | {cli_cmd}"
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
            raise RuntimeError(f"CLI / Subscription Agent Bridge Error: {err}")

    def _generate_via_openai_endpoint(self, prompt: str) -> str:
        base_url = self.config.get("openai_base_url", "http://localhost:11434/v1").rstrip("/")
        model = self.config.get("openai_model", "llama3").strip()
        api_key = self.config.get("openai_api_key", "").strip() or "dummy-key"

        url = f"{base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a professional children's storyteller."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                choices = data.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "")
                raise RuntimeError("Empty response received from OpenAI-compatible endpoint.")
        except Exception as e:
            raise RuntimeError(f"OpenAI-Compatible endpoint error ({base_url}): {str(e)}")

    def _generate_via_gemini_api(self, prompt: str) -> str:
        api_key = self.config.get("gemini_api_key", "").strip()
        if not api_key:
            raise ValueError("Gemini API Key is empty. Please set it in Settings.")
        client = genai.Client(api_key=api_key)
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
