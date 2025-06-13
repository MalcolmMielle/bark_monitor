from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from bark_monitor import logger
from bark_monitor.cli.web_service.fastapi_server import fasdtapi_webver
from bark_monitor.fake_sync import FakeSync
from bark_monitor.recorders.base_recorder import BaseRecorder
from bark_monitor.recorders.fake_recorder import FakeRecorder

recorder: dict[str, BaseRecorder] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.warning(
        "\n\n\n/*************\nIMPORTANT: If using the snap make sure to plug all the"
        " available slots with "
        "`sudo snap connect bark-monitor:XXX`.\n"
        "See available slots with `snap connections bark-monitor`\n/*************\n\n\n"
    )

    sync_service = FakeSync()

    recorder["yamnet"] = FakeRecorder(
        sync=sync_service,
        output_folder=Path(""),
        framerate=0,
    )

    yield


def main():
    fasdtapi_webver(lifespan=lifespan, recorder=recorder)


if __name__ == "__main__":
    main()
