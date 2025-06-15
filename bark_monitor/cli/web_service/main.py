import sys
from pathlib import Path

import tyro
import uvicorn

from bark_monitor import logger
from bark_monitor.cli.get_param import WebServerParameters
from bark_monitor.cli.web_service.fastapi_server import fasdtapi_webver
from bark_monitor.next_cloud_sync import NextCloudSync
from bark_monitor.recorders.yamnet_recorder import YamnetRecorder


def main():
    logger.warning(
        "\n\n\n/*************\nIMPORTANT: If using the snap make sure to plug all the"
        " available slots with "
        "`sudo snap connect bark-monitor:XXX`.\n"
        "See available slots with `snap connections bark-monitor`\n/*************\n\n\n"
    )

    if sys.argv[1] == "--help":
        print(
            "Either load a config file by using --config-file followed by the path to"
            + "the file or create a new parameter set by using: \n"
        )
        parameters = tyro.cli(WebServerParameters)
    if sys.argv[1] == "--config-file":
        parameters = WebServerParameters.read(Path(sys.argv[2]))
    else:
        parameters = tyro.cli(WebServerParameters)

    assert parameters.nextcloud_parameters is not None
    sync_service = NextCloudSync(
        server=parameters.nextcloud_parameters.server,
        user=parameters.nextcloud_parameters.user,
        passwd=parameters.nextcloud_parameters.passwd,
    )

    recorder = YamnetRecorder(
        sync=sync_service,
        output_folder=parameters.output_folder,
        sampling_time_bark_seconds=parameters.sampling_time_bark_seconds,
        http_url=parameters.thingsboard_uri,
        framerate=parameters.microphone_framerate,
    )

    app = fasdtapi_webver(recorder=recorder)
    assert parameters is not None
    uvicorn.run(app, host=parameters.server_url, port=8000)


if __name__ == "__main__":
    main()
