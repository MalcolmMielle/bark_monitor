from contextlib import asynccontextmanager

import tyro
from fastapi import FastAPI

from bark_monitor import logger
from bark_monitor.cli.get_param import Parameters
from bark_monitor.cli.web_service.fastapi_server import fasdtapi_webver
from bark_monitor.next_cloud_sync import NextCloudSync
from bark_monitor.recorders.base_recorder import BaseRecorder
from bark_monitor.recorders.yamnet_recorder import YamnetRecorder

recorder: dict[str, BaseRecorder] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.warning(
        "\n\n\n/*************\nIMPORTANT: If using the snap make sure to plug all the"
        " available slots with "
        "`sudo snap connect bark-monitor:XXX`.\n"
        "See available slots with `snap connections bark-monitor`\n/*************\n\n\n"
    )

    parameters = tyro.cli(Parameters)

    assert parameters.nextcloud_parameters is not None
    sync_service = NextCloudSync(
        server=parameters.nextcloud_parameters.server,
        user=parameters.nextcloud_parameters.user,
        passwd=parameters.nextcloud_parameters.passwd,
    )

    recorder["yamnet"] = YamnetRecorder(
        sync=sync_service,
        output_folder=parameters.output_folder,
        sampling_time_bark_seconds=parameters.sampling_time_bark_seconds,
        http_url=parameters.thingsboard_uri,
        framerate=parameters.microphone_framerate,
    )

    yield


def main():
    fasdtapi_webver(lifespan=lifespan, recorder=recorder)


if __name__ == "__main__":
    main()
