from dataclasses import dataclass

from bark_monitor.cli.get_param import Parameters


@dataclass(kw_only=True)
class WebServerParameters(Parameters):
    server_url: str = "127.0.0.1"
