import io
import logging
from pathlib import Path

import oauth2client.client
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

from bark_monitor.base_sync import BaseSync


class GoogleSync(BaseSync):
    scopes = ["https://www.googleapis.com/auth/drive.file"]
    _file_name = "recordings.json"

    def __init__(self, credential_file) -> None:
        self.credential_file = credential_file

        if self.credential_file is None:
            raise FileExistsError(
                "No credential file."
                "See https://malcolmmielle.codeberg.page/bark_monitor/@pages/google_sync/"
            )

        if not Path(self.credential_file).exists():
            raise FileExistsError(
                str(self.credential_file.absolute()) + " does not exist on the system. "
                "See https://malcolmmielle.codeberg.page/bark_monitor/@pages/google_sync/",  # noqa: E501
            )

        self._flow = None

    @staticmethod
    def get_cred() -> tuple[bool, Credentials | None]:
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
    def _get_file_id(service, file_name: str) -> str | None:
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

    def update_file(self, file_path: Path) -> None:
        """Uploads a file to google drive"""
        bark_logger = logging.getLogger("bark_monitor")
        try:
            got_creds, creds = GoogleSync.get_cred()
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
        return file.getvalue()

    def load_state(self) -> bytes | None:
        """Load the recording state stored in the "recording.json" file"""
        got_creds, creds = GoogleSync.get_cred()
        bark_logger = logging.getLogger("bark_monitor")
        if not got_creds:
            bark_logger.warning("Connect to google")
            return None
        service = build("drive", "v3", credentials=creds)
        file_id = GoogleSync._get_file_id(service, "recording.json")
        if file_id is None:
            return None
        return GoogleSync._load_file(service, file_id)

    def status(self) -> str:
        connected_to_google = "Not connected to google"
        got_cred, _ = self.get_cred()
        if got_cred:
            connected_to_google = "Connected to google"
        return connected_to_google

    def login(self) -> tuple[bool, str]:
        got_cred, _ = GoogleSync.get_cred()
        if got_cred:
            return True, ""

        self._flow = oauth2client.client.flow_from_clientsecrets(
            self.credential_file, self.scopes
        )
        self._flow.redirect_uri = oauth2client.client.OOB_CALLBACK_URN
        authorize_url = self._flow.step1_get_authorize_url()
        return False, authorize_url

    def login_step_2(self, text: str) -> None:
        if self._flow is None:
            raise ValueError("Flow is None")
        creds = self._flow.step2_exchange(text)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
