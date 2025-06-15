from dataclasses import dataclass
from pathlib import Path
from typing import Self

from bark_monitor.cli.get_param import NextCloudParameters
from bark_monitor.cli.web_service.web_server_param import WebServerParameters


@dataclass
class RSSParameters:
    nextcloud_parameters: NextCloudParameters
    output_folder: Path
    server_url: str = "127.0.0.1"

    @classmethod
    def from_webserver(cls, web_server_params: WebServerParameters) -> Self:
        assert web_server_params.nextcloud_parameters is not None
        return cls(
            nextcloud_parameters=web_server_params.nextcloud_parameters,
            server_url=web_server_params.server_url,
            output_folder=web_server_params.output_folder,
        )
