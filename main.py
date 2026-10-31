import os
import sys
import threading
import datetime
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk

from config import load_config, save_config, BASE_DIR, PROFILES_DIR, OUTPUT_DIR, DATA_DIR
from story_generator import StoryGenerator
from studio_worker import StudioAutomationEngine
from remotion_worker import RemotionVideoEngine
from youtube_uploader import YouTubeScheduler

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class AutoCastApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("AutoCast - Automated Video Content Production Studio")
        self.geometry("1100x750")
        self.minsize(950, 650)

        self.config_data = load_config()

        self.generated_story_data = None
        self.downloaded_video_path = None

        self._create_sidebar()
        self._create_main_content()

    def _create_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar_frame.pack(side="left", fill="y")

        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame, 
            text="AutoCast Studio", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.logo_label.pack(padx=20, pady=(25, 20))

        self.btn_nav_create = ctk.CTkButton(
            self.sidebar_frame, text="Generate Story & Video",
            command=lambda: self._switch_tab("create")
        )
        self.btn_nav_create.pack(padx=20, pady=10, fill="x")

        self.btn_nav_youtube = ctk.CTkButton(
            self.sidebar_frame, text="YouTube Scheduler",
            command=lambda: self._switch_tab("youtube")
        )
        self.btn_nav_youtube.pack(padx=20, pady=10, fill="x")

        self.btn_nav_settings = ctk.CTkButton(
            self.sidebar_frame, text="Settings",
            command=lambda: self._switch_tab("settings")
        )
        self.btn_nav_settings.pack(padx=20, pady=10, fill="x")

        spacer = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        spacer.pack(expand=True, fill="both")

        self.btn_login_google = ctk.CTkButton(
            self.sidebar_frame, 
            text="Setup Cloud Session",
            fg_color="#1E40AF",
            hover_color="#1E3A8A",
            command=self._launch_cloud_login
        )
        self.btn_login_google.pack(padx=20, pady=(10, 25), fill="x")

    def _create_main_content(self):
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(side="right", expand=True, fill="both", padx=20, pady=20)

        self.tab_create = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self._build_create_tab()

        self.tab_youtube = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self._build_youtube_tab()

        self.tab_settings = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self._build_settings_tab()

        self._switch_tab("create")

    def _switch_tab(self, tab_name: str):
        for tab in [self.tab_create, self.tab_youtube, self.tab_settings]:
            tab.pack_forget()

        if tab_name == "create":
            self.tab_create.pack(expand=True, fill="both")
        elif tab_name == "youtube":
            self.tab_youtube.pack(expand=True, fill="both")
        elif tab_name == "settings":
            self.tab_settings.pack(expand=True, fill="both")

    def _build_create_tab(self):
        lbl_header = ctk.CTkLabel(
            self.tab_create, 
            text="Story Script & Video Generation", 
            font=ctk.CTkFont(size=22, weight="bold")
        )
        lbl_header.pack(anchor="w", pady=(0, 15))

        grid_frame = ctk.CTkFrame(self.tab_create)
        grid_frame.pack(fill="x", pady=(0, 15), padx=5)

        lbl_theme = ctk.CTkLabel(grid_frame, text="Select Theme:", font=ctk.CTkFont(weight="bold"))
        lbl_theme.grid(row=0, column=0, padx=15, pady=10, sticky="w")

        self.combo_theme = ctk.CTkComboBox(
            grid_frame,
            width=360,
            values=[
                "Fable Animals Adventure (Clever Deer, Squirrel, Turtle)",
                "Space Exploration & Astronomy for Kids",
                "Forest Friendship & Moral Teamwork",
                "Friendly Monsters and Healthy Food Habit",
                "Magical Ocean Underwater Odyssey",
                "Custom Directive (Enter instructions below)"
            ]
        )
        self.combo_theme.grid(row=0, column=1, padx=15, pady=10, sticky="w")
        self.combo_theme.set(self.config_data.get("default_kids_theme", "Fable Animals Adventure (Clever Deer, Squirrel, Turtle)"))

        lbl_prompt = ctk.CTkLabel(grid_frame, text="Custom Directives:", font=ctk.CTkFont(weight="bold"))
        lbl_prompt.grid(row=1, column=0, padx=15, pady=10, sticky="w")

        self.entry_custom_prompt = ctk.CTkEntry(
            grid_frame, 
            width=500,
            placeholder_text="e.g. Include a gentle squirrel named Pip who loves solving puzzles..."
        )
        self.entry_custom_prompt.grid(row=1, column=1, padx=15, pady=10, sticky="ew")

        btn_frame = ctk.CTkFrame(grid_frame, fg_color="transparent")
        btn_frame.grid(row=2, column=0, columnspan=2, padx=15, pady=10, sticky="w")

        self.btn_gen_script = ctk.CTkButton(
            btn_frame, 
            text="1. Generate Story Script", 
            command=self._on_generate_script
        )
        self.btn_gen_script.pack(side="left", padx=(0, 10))

        self.btn_gen_video = ctk.CTkButton(
            btn_frame, 
            text="2. Render Remotion Video (Dynamic Motion)", 
            fg_color="#0284C7", 
            hover_color="#0369A1",
            command=self._on_generate_video
        )
        self.btn_gen_video.pack(side="left", padx=10)

        lbl_preview = ctk.CTkLabel(self.tab_create, text="Story Script Preview:", font=ctk.CTkFont(weight="bold"))
        lbl_preview.pack(anchor="w", padx=5, pady=(5, 5))

        self.txt_script_preview = ctk.CTkTextbox(self.tab_create, height=240)
        self.txt_script_preview.pack(fill="both", expand=True, padx=5, pady=(0, 10))

        self.lbl_status = ctk.CTkLabel(
            self.tab_create, 
            text="Status: Ready to create new content.", 
            text_color="#888888",
            anchor="w"
        )
        self.lbl_status.pack(fill="x", padx=5, pady=5)

    def _build_youtube_tab(self):
        lbl_header = ctk.CTkLabel(
            self.tab_youtube, 
            text="Schedule Publication to YouTube Studio", 
            font=ctk.CTkFont(size=22, weight="bold")
        )
        lbl_header.pack(anchor="w", pady=(0, 15))

        form_frame = ctk.CTkFrame(self.tab_youtube)
        form_frame.pack(fill="both", expand=True, padx=5, pady=5)

        lbl_file = ctk.CTkLabel(form_frame, text="Video File (.mp4):", font=ctk.CTkFont(weight="bold"))
        lbl_file.grid(row=0, column=0, padx=15, pady=10, sticky="w")

        self.entry_video_file = ctk.CTkEntry(form_frame, width=500, placeholder_text="Select target .mp4 video file...")
        self.entry_video_file.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        btn_browse_vid = ctk.CTkButton(form_frame, text="Browse...", width=100, command=self._browse_video_file)
        btn_browse_vid.grid(row=0, column=2, padx=10, pady=10)

        lbl_yt_title = ctk.CTkLabel(form_frame, text="Video Title:", font=ctk.CTkFont(weight="bold"))
        lbl_yt_title.grid(row=1, column=0, padx=15, pady=10, sticky="w")

        self.entry_yt_title = ctk.CTkEntry(form_frame, width=500)
        self.entry_yt_title.grid(row=1, column=1, columnspan=2, padx=10, pady=10, sticky="ew")

        lbl_yt_desc = ctk.CTkLabel(form_frame, text="Description & Tags:", font=ctk.CTkFont(weight="bold"))
        lbl_yt_desc.grid(row=2, column=0, padx=15, pady=10, sticky="nw")

        self.txt_yt_desc = ctk.CTkTextbox(form_frame, height=120)
        self.txt_yt_desc.grid(row=2, column=1, columnspan=2, padx=10, pady=10, sticky="ew")

        lbl_schedule = ctk.CTkLabel(form_frame, text="Release Schedule:", font=ctk.CTkFont(weight="bold"))
        lbl_schedule.grid(row=3, column=0, padx=15, pady=10, sticky="w")

        sched_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        sched_frame.grid(row=3, column=1, columnspan=2, padx=10, pady=10, sticky="w")

        tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
        self.entry_sched_date = ctk.CTkEntry(sched_frame, width=120)
        self.entry_sched_date.insert(0, tomorrow.strftime("%Y-%m-%d"))
        self.entry_sched_date.pack(side="left", padx=(0, 10))

        self.entry_sched_time = ctk.CTkEntry(sched_frame, width=80)
        self.entry_sched_time.insert(0, "17:00")
        self.entry_sched_time.pack(side="left", padx=5)

        lbl_tz = ctk.CTkLabel(sched_frame, text="Local Time (WIB / GMT+7)", text_color="#aaaaaa")
        lbl_tz.pack(side="left", padx=10)

        self.chk_kids = ctk.CTkCheckBox(form_frame, text="Mark as 'Made for Kids' (Complies with COPPA regulations)")
        self.chk_kids.select()
        self.chk_kids.grid(row=4, column=1, columnspan=2, padx=10, pady=10, sticky="w")

        self.btn_upload_yt = ctk.CTkButton(
            form_frame,
            text="Schedule Upload to YouTube",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#CC0000",
            hover_color="#AA0000",
            height=40,
            command=self._on_upload_youtube
        )
        self.btn_upload_yt.grid(row=5, column=1, padx=10, pady=20, sticky="w")

    def _build_settings_tab(self):
        lbl_header = ctk.CTkLabel(
            self.tab_settings, 
            text="API Credentials & Configuration", 
            font=ctk.CTkFont(size=22, weight="bold")
        )
        lbl_header.pack(anchor="w", pady=(0, 15))

        settings_box = ctk.CTkFrame(self.tab_settings)
        settings_box.pack(fill="x", padx=5, pady=5)

        # AI Engine Mode Selector
        lbl_mode = ctk.CTkLabel(settings_box, text="Story Generation Engine:", font=ctk.CTkFont(weight="bold"))
        lbl_mode.grid(row=0, column=0, padx=15, pady=12, sticky="w")

        self.combo_engine_mode = ctk.CTkComboBox(
            settings_box,
            width=450,
            values=[
                "Pi Agent Bridge (Gemini 3.8 Flash Subscription)",
                "OpenAI-Compatible Custom Endpoint (Ollama / LiteLLM)",
                "Official Google Gemini API Key",
                "Manual Story Script Mode (Copy & Paste)"
            ],
            command=self._on_engine_mode_change
        )
        self.combo_engine_mode.grid(row=0, column=1, padx=10, pady=12, sticky="w")
        current_mode = self.config_data.get("engine_mode", "pi_agent")
        if current_mode == "pi_agent":
            self.combo_engine_mode.set("Pi Agent Bridge (Gemini 3.8 Flash Subscription)")
        elif current_mode == "openai_compatible":
            self.combo_engine_mode.set("OpenAI-Compatible Custom Endpoint (Ollama / LiteLLM)")
        elif current_mode == "manual":
            self.combo_engine_mode.set("Manual Story Script Mode (Copy & Paste)")
        else:
            self.combo_engine_mode.set("Official Google Gemini API Key")

        # Row 1: CLI Pipe Command (For Pi / Terminal Agent)
        lbl_cli = ctk.CTkLabel(settings_box, text="CLI Agent Command:", font=ctk.CTkFont(weight="bold"))
        lbl_cli.grid(row=1, column=0, padx=15, pady=10, sticky="w")

        self.entry_cli_command = ctk.CTkEntry(settings_box, width=450)
        self.entry_cli_command.insert(0, self.config_data.get("cli_command", "pi --provider antigravity --model gemini-3.8-flash -p"))
        self.entry_cli_command.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        # Row 2: Custom Base URL (OpenAI / Ollama / Local proxy)
        lbl_base_url = ctk.CTkLabel(settings_box, text="Custom Base URL:", font=ctk.CTkFont(weight="bold"))
        lbl_base_url.grid(row=2, column=0, padx=15, pady=10, sticky="w")

        self.entry_base_url = ctk.CTkEntry(settings_box, width=450, placeholder_text="e.g. http://localhost:11434/v1")
        self.entry_base_url.insert(0, self.config_data.get("openai_base_url", "http://localhost:11434/v1"))
        self.entry_base_url.grid(row=2, column=1, padx=10, pady=10, sticky="w")

        # Row 3: Custom Model Name & Key
        lbl_custom_model = ctk.CTkLabel(settings_box, text="Custom Model / Key:", font=ctk.CTkFont(weight="bold"))
        lbl_custom_model.grid(row=3, column=0, padx=15, pady=10, sticky="w")

        custom_model_frame = ctk.CTkFrame(settings_box, fg_color="transparent")
        custom_model_frame.grid(row=3, column=1, padx=10, pady=10, sticky="w")

        self.entry_custom_model = ctk.CTkEntry(custom_model_frame, width=220, placeholder_text="Model (e.g. llama3)")
        self.entry_custom_model.insert(0, self.config_data.get("openai_model", "llama3"))
        self.entry_custom_model.pack(side="left", padx=(0, 10))

        self.entry_custom_key = ctk.CTkEntry(custom_model_frame, width=220, show="*", placeholder_text="API Key (Optional)")
        self.entry_custom_key.insert(0, self.config_data.get("openai_api_key", ""))
        self.entry_custom_key.pack(side="left")

        # Row 4: Official Gemini API Key
        lbl_gemini = ctk.CTkLabel(settings_box, text="Official Gemini API Key:", font=ctk.CTkFont(weight="bold"))
        lbl_gemini.grid(row=4, column=0, padx=15, pady=10, sticky="w")

        self.entry_gemini_key = ctk.CTkEntry(settings_box, width=450, show="*")
        self.entry_gemini_key.insert(0, self.config_data.get("gemini_api_key", ""))
        self.entry_gemini_key.grid(row=4, column=1, padx=10, pady=10, sticky="w")

        # Row 5: YouTube Client Secret
        lbl_yt_secret = ctk.CTkLabel(settings_box, text="YouTube Client Secret JSON:", font=ctk.CTkFont(weight="bold"))
        lbl_yt_secret.grid(row=5, column=0, padx=15, pady=10, sticky="w")

        self.entry_secret_path = ctk.CTkEntry(settings_box, width=450)
        self.entry_secret_path.insert(0, self.config_data.get("youtube_client_secret_path", ""))
        self.entry_secret_path.grid(row=5, column=1, padx=10, pady=10, sticky="w")

        btn_browse_secret = ctk.CTkButton(settings_box, text="Browse...", width=100, command=self._browse_secret_file)
        btn_browse_secret.grid(row=5, column=2, padx=10, pady=10)

        # Row 6: Export Directory
        lbl_out = ctk.CTkLabel(settings_box, text="Export Directory:", font=ctk.CTkFont(weight="bold"))
        lbl_out.grid(row=6, column=0, padx=15, pady=10, sticky="w")

        self.entry_output_dir = ctk.CTkEntry(settings_box, width=450)
        self.entry_output_dir.insert(0, self.config_data.get("output_dir", str(OUTPUT_DIR)))
        self.entry_output_dir.grid(row=6, column=1, padx=10, pady=10, sticky="w")

        btn_browse_out = ctk.CTkButton(settings_box, text="Browse...", width=100, command=self._browse_output_dir)
        btn_browse_out.grid(row=6, column=2, padx=10, pady=10)

        btn_save = ctk.CTkButton(
            self.tab_settings, 
            text="Save Settings", 
            width=200, 
            command=self._save_settings_action
        )
        btn_save.pack(pady=20, anchor="w")

    def _update_status(self, message: str):
        self.lbl_status.configure(text=f"Status: {message}")
        self.update_idletasks()

    def _browse_video_file(self):
        f = filedialog.askopenfilename(filetypes=[("MP4 Video", "*.mp4"), ("All Files", "*.*")])
        if f:
            self.entry_video_file.delete(0, "end")
            self.entry_video_file.insert(0, f)

    def _browse_secret_file(self):
        f = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if f:
            self.entry_secret_path.delete(0, "end")
            self.entry_secret_path.insert(0, f)

    def _browse_output_dir(self):
        d = filedialog.askdirectory()
        if d:
            self.entry_output_dir.delete(0, "end")
            self.entry_output_dir.insert(0, d)

    def _on_engine_mode_change(self, choice: str):
        pass

    def _save_settings_action(self):
        selected = self.combo_engine_mode.get()
        if "Pi Agent" in selected:
            mode_val = "pi_agent"
        elif "OpenAI" in selected:
            mode_val = "openai_compatible"
        elif "Manual" in selected:
            mode_val = "manual"
        else:
            mode_val = "gemini_api"

        self.config_data["engine_mode"] = mode_val
        self.config_data["cli_command"] = self.entry_cli_command.get().strip()
        self.config_data["openai_base_url"] = self.entry_base_url.get().strip()
        self.config_data["openai_model"] = self.entry_custom_model.get().strip()
        self.config_data["openai_api_key"] = self.entry_custom_key.get().strip()
        self.config_data["gemini_api_key"] = self.entry_gemini_key.get().strip()
        self.config_data["youtube_client_secret_path"] = self.entry_secret_path.get().strip()
        self.config_data["output_dir"] = self.entry_output_dir.get().strip()
        save_config(self.config_data)
        messagebox.showinfo("Success", "Settings updated successfully.")

    def _launch_cloud_login(self):
        def worker():
            engine = StudioAutomationEngine(profile_dir=PROFILES_DIR, headless=False)
            engine.launch_session_setup(status_callback=self._update_status)

        threading.Thread(target=worker, daemon=True).start()

    def _on_generate_script(self):
        mode = self.config_data.get("engine_mode", "pi_agent")

        theme = self.combo_theme.get()
        custom_prompt = self.entry_custom_prompt.get().strip()

        self._update_status(f"Generating story using [{mode}] provider...")
        self.btn_gen_script.configure(state="disabled")

        def worker():
            try:
                generator = StoryGenerator(config=self.config_data)
                story_data = generator.generate_story(theme, custom_prompt)
                self.generated_story_data = story_data

                self.txt_script_preview.delete("1.0", "end")
                if mode == "manual":
                    self.txt_script_preview.insert("1.0", story_data["content"])
                    self._update_status("Manual prompt generated! Copy to your preferred AI chat, then paste the story here.")
                else:
                    self.txt_script_preview.insert("1.0", f"TITLE: {story_data['title']}\n\n{story_data['content']}")
                    self.entry_yt_title.delete(0, "end")
                    self.entry_yt_title.insert(0, story_data["title"])
                    self.txt_yt_desc.delete("1.0", "end")
                    self.txt_yt_desc.insert("1.0", f"{story_data['description']}\n\nTags: {story_data['tags']}")
                    self._update_status(f"Script generated successfully via {mode}.")
            except Exception as e:
                self._update_status(f"Error during script generation: {str(e)}")
                messagebox.showerror("Script Generation Failed", str(e))
            finally:
                self.btn_gen_script.configure(state="normal")

        threading.Thread(target=worker, daemon=True).start()

    def _on_generate_video(self):
        content = self.txt_script_preview.get("1.0", "end").strip()
        if not content:
            messagebox.showwarning("Empty Content", "Please generate a story script first.")
            return

        title = self.entry_yt_title.get().strip() or "Petualangan Dongeng Anak"
        out_dir = Path(self.config_data.get("output_dir", str(OUTPUT_DIR)))
        out_dir.mkdir(parents=True, exist_ok=True)
        sanitized_title = "".join(c for c in title if c.isalnum() or c in (" ", "_", "-")).rstrip()
        target_mp4 = out_dir / f"{sanitized_title}_{int(datetime.datetime.now().timestamp())}.mp4"

        # Split content into dynamic narrative scenes
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip() and not p.startswith("TITLE:")]
        if not paragraphs:
            paragraphs = [content[:120], content[120:240]]

        # Dynamic sample illustrated backgrounds for scenes
        sample_images = [
            "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=1280&q=80",
            "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=1280&q=80",
            "https://images.unsplash.com/photo-1511497584788-87676104235f?w=1280&q=80",
            "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1280&q=80"
        ]

        scenes = []
        for i, para in enumerate(paragraphs[:6]):
            img = sample_images[i % len(sample_images)]
            # Estimate duration based on word count (approx 150 words per min = ~2.5 words per sec @ 30fps)
            word_count = len(para.split())
            frames = max(90, min(300, int((word_count / 2.5) * 30)))
            scenes.append({
                "imageSrc": img,
                "caption": para[:140] + ("..." if len(para) > 140 else ""),
                "durationInFrames": frames
            })

        self._update_status("Starting Remotion Programmatic Video Engine...")
        self.btn_gen_video.configure(state="disabled")

        def worker():
            try:
                engine = RemotionVideoEngine()
                video_file = engine.render_story_video(
                    composition_id="StoryVideo",
                    title=title,
                    scenes=scenes,
                    output_mp4_path=str(target_mp4),
                    status_callback=self._update_status
                )
                self.downloaded_video_path = video_file
                self.entry_video_file.delete(0, "end")
                self.entry_video_file.insert(0, video_file)

                self._update_status(f"Video rendered successfully: {os.path.basename(video_file)}")
                messagebox.showinfo(
                    "Remotion Render Finished",
                    f"Dynamic motion video generated successfully!\n\nSaved to:\n{video_file}\n\nYou can now review and schedule it in the YouTube tab."
                )
                self._switch_tab("youtube")
            except Exception as e:
                self._update_status(f"Remotion render error: {str(e)}")
                messagebox.showerror("Video Render Error", str(e))
            finally:
                self.btn_gen_video.configure(state="normal")

        threading.Thread(target=worker, daemon=True).start()

    def _on_upload_youtube(self):
        video_path = self.entry_video_file.get().strip()
        title = self.entry_yt_title.get().strip()
        desc = self.txt_yt_desc.get("1.0", "end").strip()
        date_str = self.entry_sched_date.get().strip()
        time_str = self.entry_sched_time.get().strip()
        secret_file = self.entry_secret_path.get().strip()
        made_for_kids = bool(self.chk_kids.get())

        if not os.path.exists(video_path):
            messagebox.showwarning("Missing File", "Please choose a valid MP4 video file.")
            return

        if not title:
            messagebox.showwarning("Missing Title", "Video title cannot be empty.")
            return

        if not os.path.exists(secret_file):
            messagebox.showwarning(
                "Missing Credentials", 
                "YouTube client_secret.json was not found. Please configure it in Settings."
            )
            self._switch_tab("settings")
            return

        try:
            local_dt = datetime.datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            utc_dt = local_dt - datetime.timedelta(hours=7)
        except Exception:
            messagebox.showerror("Invalid Date Format", "Format must be YYYY-MM-DD and HH:MM (e.g. 2026-11-01 17:00).")
            return

        self._update_status("Initiating YouTube upload...")
        self.btn_upload_yt.configure(state="disabled")

        def worker():
            try:
                scheduler = YouTubeScheduler(client_secret_file=secret_file, token_dir=DATA_DIR)
                vid_id = scheduler.upload_and_schedule(
                    video_path=video_path,
                    title=title,
                    description=desc,
                    tags=["stories", "animation", "education"],
                    schedule_time_utc=utc_dt,
                    made_for_kids=made_for_kids,
                    status_callback=self._update_status
                )
                messagebox.showinfo(
                    "Scheduled Successfully", 
                    f"Video scheduled for {date_str} at {time_str} local time.\n\nVideo ID: {vid_id}"
                )
            except Exception as e:
                self._update_status(f"YouTube upload error: {str(e)}")
                messagebox.showerror("Upload Failed", str(e))
            finally:
                self.btn_upload_yt.configure(state="normal")

        threading.Thread(target=worker, daemon=True).start()

if __name__ == "__main__":
    app = AutoCastApp()
    app.mainloop()
