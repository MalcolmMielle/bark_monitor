from json import dumps
from pathlib import Path

from nc_py_api import Nextcloud, NextcloudException

from bark_monitor.base_sync import BaseSync


class NextCloudSync(BaseSync):
    def __init__(self, server: str, user: str, passwd: str) -> None:
        self._server = server
        self._user = user
        self._passwd = passwd

        self._nc = Nextcloud(
            nextcloud_url=self._server,
            nc_auth_user=self._user,
            nc_auth_pass=self._passwd,
        )

        super().__init__()

    def update_file(self, file_path: Path) -> None:
        self._nc.files.upload_stream(file_path.name, file_path.absolute())

    def load_state(self) -> bytes | None:
        try:
            return self._nc.files.download("recording.json")
        except NextcloudException:
            return None

    def status(self) -> str:
        return dumps(self._nc.capabilities, indent=4, sort_keys=True)

    def login(self) -> tuple[bool, str]:
        return True, ""

    def login_step_2(self, text: str) -> None:
        pass
