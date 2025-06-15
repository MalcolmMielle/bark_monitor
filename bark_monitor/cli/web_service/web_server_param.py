from dataclasses import dataclass

from bark_monitor.cli.get_param import Parameters


@dataclass(kw_only=True)
class WebServerParameters(Parameters):
    server_url: str = "127.0.0.1"
    other_origins: list[str] | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.other_origins is None:
            self.other_origins = ["127.0.0.1:8080"]
