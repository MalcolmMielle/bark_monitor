import sys
from pathlib import Path

import tyro
import uvicorn
from fastapi import FastAPI
from fastapi_rss import RSSFeed, RSSResponse

from bark_monitor.cli.web_service.rss_param import RSSParameters
from bark_monitor.cli.web_service.web_server_param import WebServerParameters
from bark_monitor.next_cloud_sync import NextCloudSync
from bark_monitor.recorders.recording import Recording


def main() -> None:
    if sys.argv[1] == "--help":
        print(
            "\nEither load a config file by using --config-file followed by the path to"
            + "the file or create a new parameter set by using: \n"
        )
        parameters = tyro.cli(RSSParameters)
    if sys.argv[1] == "--config-file":
        parameters_web = WebServerParameters.read(Path(sys.argv[2]))
        parameters = RSSParameters.from_webserver(parameters_web)
    else:
        parameters = tyro.cli(RSSParameters)

    assert parameters.nextcloud_parameters is not None
    sync_service = NextCloudSync(
        server=parameters.nextcloud_parameters.server,
        user=parameters.nextcloud_parameters.user,
        passwd=parameters.nextcloud_parameters.passwd,
    )

    app = FastAPI()

    @app.get("/")
    async def rss_feed() -> RSSResponse:
        recording = Recording.read(
            output_folder=parameters.output_folder,
            sync_service=sync_service,
        )
        feed = RSSFeed(**(recording.feed_data))
        return RSSResponse(content=feed)

    uvicorn.run(app, host=parameters.server_url, port=8001)


if __name__ == "__main__":
    main()
