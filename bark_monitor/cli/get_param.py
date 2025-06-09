import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar, Self

import jsonpickle

from bark_monitor import logger


@dataclass(kw_only=True)
class Parameters:
    __uninitialized_output_folder: ClassVar[Path] = Path("")
    output_folder: Path = field(
        default_factory=lambda: Parameters.__uninitialized_output_folder
    )

    __uninitialized_config_folder: ClassVar[Path] = Path("")
    config_folder: Path = field(
        default_factory=lambda: Parameters.__uninitialized_config_folder
    )

    __uninitialized_api: ClassVar[str] = ""
    api_key: str = field(default_factory=lambda: Parameters.__uninitialized_api)

    config_file: Path | None = None
    microphone_framerate: int = 16000
    sampling_time_bark_seconds: int = 1
    accept_new_users: bool = False
    google_creds: str | None = None
    things_board_url: str | None = None

    def __post_init__(self) -> None:
        if self.config_file is not None:
            with open(self.config_file, "rb") as f:
                json_data = json.load(f)

            if (
                "thingsboard_ip" in json_data
                and "thingsboard_port" in json_data
                and "thingsboard_device_token" in json_data
            ):
                self.things_board_url = (
                    "http://"
                    + json_data["thingsboard_ip"]
                    + ":"
                    + str(json_data["thingsboard_port"])
                    + "/api/v1/"
                    + json_data["thingsboard_device_token"]
                    + "/telemetry"
                )

            if "microphone framerate" in json_data:
                self.microphone_framerate = json_data["microphone framerate"]

            if "sampling time bark seconds" in json_data:
                self.sampling_time_bark_seconds = json_data[
                    "sampling time bark seconds"
                ]

            if "google credentials" in json_data:
                self.google_creds = json_data["google credentials"]

            if "output_folder" in json_data:
                self.output_folder = json_data["output_folder"]

            if "config_folder" in json_data:
                self.config_folder = json_data["config_folder"]

            if "api_key" in json_data:
                self.api_key = json_data["api_key"]

        self.is_valid()

    def is_valid(self) -> None:
        if self.api_key is self.__uninitialized_api:
            raise ValueError("api_key is not set")
        if self.output_folder is self.__uninitialized_output_folder:
            raise ValueError("output_folder is not set")

        if self.output_folder == Path(""):
            logger.warning("output_folder is set to Path() which is the default value")

    def save(self, path: str) -> None:
        encoded = jsonpickle.encode(self)
        assert encoded is not None
        with open(path, "w") as outfile:
            outfile.write(encoded)

    @classmethod
    def read(cls, path: str) -> Self:
        with open(path, "r") as file:
            # dict = json.load(file)
            lines = file.read()
            parameters: Parameters = jsonpickle.decode(lines)  # type: ignore
            parameters.is_valid()
        return parameters
