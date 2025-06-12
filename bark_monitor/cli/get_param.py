from dataclasses import dataclass
from pathlib import Path
from typing import Self

import jsonpickle


@dataclass(kw_only=True)
class NextCloudParameters:
    server: str
    user: str
    passwd: str


@dataclass(kw_only=True)
class ThingsBoardParameters:
    thingsboard_ip: str
    thingsboard_port: int
    thingsboard_device_token: str

    def __post_init__(self) -> None:
        self.things_board_url = (
            "http://"
            + self.thingsboard_ip
            + ":"
            + str(self.thingsboard_port)
            + "/api/v1/"
            + self.thingsboard_device_token
            + "/telemetry"
        )


@dataclass(kw_only=True)
class Parameters:
    output_folder: Path
    config_folder: Path

    api_key: str | None = None
    config_file: Path | None = None
    microphone_framerate: int = 16000
    sampling_time_bark_seconds: int = 1
    accept_new_users: bool = False
    google_creds: str | None = None

    nextcloud_parameters: NextCloudParameters | None = None
    """Nextcloud parameters"""

    thingsboard_parameters: ThingsBoardParameters | None = None
    """Thingboard parameters"""

    @property
    def thingsboard_uri(self) -> str | None:
        if self.thingsboard_parameters is not None:
            return self.thingsboard_parameters.things_board_url
        return None

    def save(self, path: str) -> None:
        encoded = jsonpickle.encode(self)
        assert encoded is not None
        with open(path, "w") as outfile:
            outfile.write(encoded)

    @classmethod
    def read(cls, path: Path) -> Self:
        with open(path, "r") as file:
            lines = file.read()
            parameters: Parameters = jsonpickle.decode(lines)  # type: ignore
        return parameters
