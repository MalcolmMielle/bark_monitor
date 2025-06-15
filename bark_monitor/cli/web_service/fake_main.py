from pathlib import Path

import tyro
import uvicorn

from bark_monitor.cli.web_service.fastapi_server import fasdtapi_webver
from bark_monitor.fake_sync import FakeSync
from bark_monitor.recorders.base_recorder import BaseRecorder
from bark_monitor.recorders.fake_recorder import FakeRecorder

recorder: dict[str, BaseRecorder] = {}


def main(server_url: str = "127.0.0.1"):
    sync_service = FakeSync()
    recorder = FakeRecorder(
        sync=sync_service,
        output_folder=Path(""),
        framerate=0,
    )
    app = fasdtapi_webver(recorder=recorder)

    @app.post("/trigger_fake_bark")
    async def fake_bark() -> None:
        recorder.add_bark()

    uvicorn.run(app, host=server_url, port=8000)


if __name__ == "__main__":
    tyro.cli(main)
