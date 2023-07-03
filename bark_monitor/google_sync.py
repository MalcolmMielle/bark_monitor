import io
import logging
import shutil
from pathlib import Path
from typing import Optional

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload


class GoogleSync:
    scopes = ["https://www.googleapis.com/auth/drive.file"]
    _file_name = "recordings.json"

    @staticmethod
    def _get_cred() -> tuple[bool, Optional[Credentials]]:
        """Check if connected to google drive already"""
        creds = None
        if Path("token.json").exists():
            creds = Credentials.from_authorized_user_file(
                "token.json", GoogleSync.scopes
            )
        # If there are no (valid) credentials available, let the user log in.
        if creds and creds.valid:
            return True, Credentials.from_authorized_user_file(
                "token.json", GoogleSync.scopes
            )
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                return True, Credentials.from_authorized_user_file(
                    "token.json", GoogleSync.scopes
                )
            except RefreshError:
                return False, None
        return False, None

    @staticmethod
    def _get_file_id(service, file_name: str) -> Optional[str]:
        results = (
            service.files()
            .list(
                q="trashed=false", pageSize=10, fields="nextPageToken, files(id, name)"
            )
            .execute()
        )
        items = results.get("files", [])
        for item in items:
            if item["name"] == file_name:
                return item["id"]
        return None

    @staticmethod
    def upload_file(service, file_path: Path) -> None:
        file_metadata = {"name": file_path.name}
        media = MediaFileUpload(file_path.absolute())
        file = (
            service.files()
            .create(body=file_metadata, media_body=media, fields="id")
            .execute()
        )
        return file

    @staticmethod
    def update_file(file_path: Path) -> None:
        bark_logger = logging.getLogger("bark_monitor")
        try:
            got_creds, creds = GoogleSync._get_cred()
            if not got_creds:
                bark_logger.warning("Connect to google to trigger sync to drive")
                return
            # create drive api client
            service = build("drive", "v3", credentials=creds)
            file_id = GoogleSync._get_file_id(service, file_path.name)
            if file_id is None:
                return GoogleSync.upload_file(service, file_path)

            file_metadata = {"name": file_path.name}
            media = MediaFileUpload(file_path.absolute())
            file = (
                service.files()
                .update(
                    fileId=file_id, body=file_metadata, media_body=media, fields="id"
                )
                .execute()
            )
            return file
        except HttpError as error:
            bark_logger.error(error)

    @staticmethod
    def _load_file(service, file_id: str) -> bytes:
        request = service.files().get_media(fileId=file_id)
        file = io.BytesIO()
        downloader = MediaIoBaseDownload(file, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print(f"Download {int(status.progress() * 100)}.")
        return file.getvalue()

    @staticmethod
    def load_state() -> Optional[bytes]:
        """Load the recording state stored in the "recording.json" file"""
        got_creds, creds = GoogleSync._get_cred()
        bark_logger = logging.getLogger("bark_monitor")
        if not got_creds:
            bark_logger.warning("Connect to google")
            return None
        service = build("drive", "v3", credentials=creds)
        file_id = GoogleSync._get_file_id(service, "recording.json")
        if file_id is None:
            return None
        return GoogleSync._load_file(service, file_id)

    @staticmethod
    def save_audio(audio_folder: str) -> None:
        """Save `audio_folder` as a zip file in google drive"""
        shutil.make_archive("bark_monitor_audio", "zip", audio_folder)
        GoogleSync.update_file(Path("bark_monitor_audio.zip"))
