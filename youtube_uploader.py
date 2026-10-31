import os
import datetime
from pathlib import Path
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

class YouTubeScheduler:
    def __init__(self, client_secret_file: str, token_dir: Path):
        self.client_secret_file = client_secret_file
        self.token_file = Path(token_dir) / "youtube_token.pickle"

    def authenticate(self, status_callback=None):
        creds = None
        if self.token_file.exists():
            with open(self.token_file, "rb") as token:
                try:
                    creds = pickle.load(token)
                except Exception:
                    creds = None

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                if status_callback:
                    status_callback("Refreshing YouTube authentication token...")
                creds.refresh(Request())
            else:
                if not os.path.exists(self.client_secret_file):
                    raise FileNotFoundError(
                        f"Secret file '{self.client_secret_file}' not found. "
                        "Please provide OAuth Client Secrets from Google Cloud Console."
                    )
                if status_callback:
                    status_callback("Opening browser for YouTube authorization...")
                flow = InstalledAppFlow.from_client_secrets_file(self.client_secret_file, SCOPES)
                creds = flow.run_local_server(port=0)

            with open(self.token_file, "wb") as token:
                pickle.dump(creds, token)

        return build("youtube", "v3", credentials=creds)

    def upload_and_schedule(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: list,
        schedule_time_utc: datetime.datetime = None,
        made_for_kids: bool = True,
        status_callback=None
    ) -> str:
        """
        Uploads video and schedules release on YouTube.
        schedule_time_utc: datetime object in UTC.
        """
        youtube = self.authenticate(status_callback)

        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file '{video_path}' not found.")

        status_body = {
            "selfDeclaredMadeForKids": made_for_kids
        }

        if schedule_time_utc:
            iso_time = schedule_time_utc.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            status_body["privacyStatus"] = "private"
            status_body["publishAt"] = iso_time
        else:
            status_body["privacyStatus"] = "public"

        body = {
            "snippet": {
                "title": title[:100],
                "description": description[:5000],
                "tags": tags[:50] if tags else ["stories", "animation", "education"],
                "categoryId": "27"
            },
            "status": status_body
        }

        if status_callback:
            status_callback(f"Starting upload to YouTube Studio ({os.path.basename(video_path)})...")

        media = MediaFileUpload(video_path, chunksize=1024*1024*5, resumable=True)
        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status and status_callback:
                progress = int(status.progress() * 100)
                status_callback(f"Uploading video: {progress}%")

        video_id = response.get("id")
        if status_callback:
            status_callback(f"Completed! Video scheduled successfully. Video ID: {video_id}")

        return video_id
