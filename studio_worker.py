import os
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

WORKSPACE_URL = "https://notebooklm.google.com/"

class StudioAutomationEngine:
    def __init__(self, profile_dir: Path, headless: bool = False):
        self.profile_dir = Path(profile_dir)
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        self.headless = headless

    def launch_session_setup(self, status_callback=None):
        """
        Launches an interactive browser instance for single sign-on authentication.
        The persistent profile stores cookies and active sessions locally.
        """
        if status_callback:
            status_callback("Launching authentication browser... Please complete your sign-in.")

        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(self.profile_dir),
                headless=False,
                channel="chrome",
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--start-maximized"
                ],
                no_viewport=True
            )
            page = context.pages[0] if context.pages else context.new_page()
            page.goto(WORKSPACE_URL)

            if status_callback:
                status_callback("Browser ready. Complete sign-in in the opened window.")

            try:
                while len(context.pages) > 0 and not page.is_closed():
                    if "accounts.google.com" not in page.url:
                        if status_callback:
                            status_callback("Cloud studio session established.")
                    time.sleep(2)
            except Exception:
                pass

            try:
                context.close()
            except Exception:
                pass

        if status_callback:
            status_callback("Session profile saved successfully.")

    def render_and_export_video(self, title: str, story_content: str, output_dir: Path, status_callback=None) -> str:
        """
        Automates project setup, source integration, synthesis, and asset export.
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        if status_callback:
            status_callback("Connecting to cloud studio engine...")

        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(self.profile_dir),
                headless=self.headless,
                args=[
                    "--disable-blink-features=AutomationControlled"
                ],
                viewport={"width": 1366, "height": 768}
            )

            page = context.pages[0] if context.pages else context.new_page()
            page.goto(WORKSPACE_URL, timeout=60000)
            page.wait_for_load_state("networkidle", timeout=30000)

            if "accounts.google.com" in page.url:
                context.close()
                raise RuntimeError("Authentication required. Please click 'Setup Cloud Session' first.")

            if status_callback:
                status_callback("Initializing new project space...")

            new_project_btn = page.locator("button:has-text('New'), button:has-text('Create'), [aria-label*='Create'], [aria-label*='New']").first
            if new_project_btn.is_visible(timeout=10000):
                new_project_btn.click()
            else:
                page.keyboard.press("Tab")
                time.sleep(1)

            page.wait_for_timeout(3000)

            if status_callback:
                status_callback("Injecting narrative script into workspace...")

            paste_tab = page.locator("button:has-text('Copied text'), button:has-text('Text'), [aria-label*='text']").first
            if paste_tab.is_visible(timeout=10000):
                paste_tab.click()
                time.sleep(1)

            title_input = page.locator("input[placeholder*='Title']").first
            if title_input.is_visible(timeout=5000):
                title_input.fill(title)

            textarea = page.locator("textarea").first
            if textarea.is_visible(timeout=5000):
                textarea.fill(story_content)
                time.sleep(1)

            insert_btn = page.locator("button:has-text('Insert'), button:has-text('Save'), button:has-text('Add')").first
            if insert_btn.is_visible(timeout=5000):
                insert_btn.click()

            if status_callback:
                status_callback("Source compiled. Triggering synthesis...")

            page.wait_for_timeout(5000)

            video_option = page.locator("button:has-text('Video'), [aria-label*='Video']").first
            generate_action = page.locator("button:has-text('Generate'), button:has-text('Create')").first

            if video_option.is_visible(timeout=10000):
                video_option.click()
                time.sleep(1)

            if generate_action.is_visible(timeout=5000):
                generate_action.click()

            if status_callback:
                status_callback("Rendering video presentation in cloud (estimated 3-7 minutes)...")

            completed = False
            max_wait_seconds = 600
            start_time = time.time()

            sanitized_title = "".join(c for c in title if c.isalnum() or c in (" ", "_", "-")).rstrip()
            target_filepath = output_dir / f"{sanitized_title}_{int(time.time())}.mp4"

            while time.time() - start_time < max_wait_seconds:
                elapsed = int(time.time() - start_time)
                if status_callback and elapsed % 15 == 0:
                    status_callback(f"Synthesizing media presentation... ({elapsed}s)")

                download_btn = page.locator("button[aria-label*='Download'], button:has-text('Download'), a[download]").first
                if download_btn.is_visible(timeout=2000):
                    if status_callback:
                        status_callback("Rendering finished. Downloading MP4...")

                    try:
                        with page.expect_download(timeout=60000) as download_info:
                            download_btn.click()
                        download = download_info.value
                        download.save_as(str(target_filepath))
                        completed = True
                        break
                    except Exception:
                        pass

                time.sleep(5)

            context.close()

            if completed and target_filepath.exists():
                if status_callback:
                    status_callback(f"Download complete: {target_filepath.name}")
                return str(target_filepath)
            else:
                raise TimeoutError("Render duration exceeded limit or download button was not detected.")
