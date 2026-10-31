import os
from google import genai
from google.genai import types

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
    def __init__(self, api_key: str):
        self.api_key = api_key.strip()
        if not self.api_key:
            raise ValueError("Gemini API Key is required. Please set it in Settings.")
        self.client = genai.Client(api_key=self.api_key)

    def generate_story(self, theme: str, custom_prompt: str = "") -> dict:
        prompt = STORY_PROMPT_TEMPLATE.format(
            theme=theme,
            custom_prompt=custom_prompt if custom_prompt else "Create a cheerful, moral-rich story suitable for toddlers and primary school children."
        )

        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )

        raw_text = response.text or ""
        return self._parse_story(raw_text)

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
