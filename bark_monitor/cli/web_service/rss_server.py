from pathlib import Path

import tyro
import uvicorn
from fastapi import FastAPI
from fastapi_rss import RSSFeed, RSSResponse

from bark_monitor.cli.get_param import NextCloudParameters
from bark_monitor.next_cloud_sync import NextCloudSync
from bark_monitor.recorders.recording import Recording


def main(
    server_url: str, output_folder: Path, nextcloud_parameters: NextCloudParameters
):
    sync_service = NextCloudSync(
        server=nextcloud_parameters.server,
        user=nextcloud_parameters.user,
        passwd=nextcloud_parameters.passwd,
    )

    app = FastAPI()

    @app.get("/rss")
    async def rss_feed():
        recording = Recording.read(
            output_folder=output_folder,
            sync_service=sync_service,
        )
        feed = RSSFeed(**(recording.feed_data))
        return RSSResponse(feed)

    uvicorn.run(app, host=server_url, port=8001)


if __name__ == "__main__":
    tyro.cli(main)
