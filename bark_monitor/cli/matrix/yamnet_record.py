import sys
from pathlib import Path

import tyro

from bark_monitor import logger
from bark_monitor.bots.very_bark_matrix_bot import VeryBarkMatrixBot
from bark_monitor.cli.get_param import Parameters
from bark_monitor.google_sync import GoogleSync
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
        parameters = tyro.cli(Parameters)
    if sys.argv[1] == "--config-file":
        parameters = Parameters.read(Path(sys.argv[4]))
    else:
        parameters = tyro.cli(Parameters)

    if parameters.nextcloud_parameters is not None:
        sync_service = NextCloudSync(
            server=parameters.nextcloud_parameters.server,
            user=parameters.nextcloud_parameters.user,
            passwd=parameters.nextcloud_parameters.passwd,
        )
    elif parameters.google_creds is not None:
        sync_service = GoogleSync(credential_file=parameters.google_creds)
    else:
        raise RuntimeError("Please provide either google_creds or nextcloud_parameters")

    if parameters.api_key is None:
        raise RuntimeError("Please provide a Telegram bot API key")

    assert parameters.matrix_parameters is not None
    bot = VeryBarkMatrixBot(
        sync=sync_service,
        config_folder=parameters.config_folder,
        homeserver=parameters.matrix_parameters.homeserver,
        user_id=parameters.matrix_parameters.user_id,
        password=parameters.matrix_parameters.password,
    )

    recorder = YamnetRecorder(
        sync=sync_service,
        output_folder=parameters.output_folder,
        sampling_time_bark_seconds=parameters.sampling_time_bark_seconds,
        http_url=parameters.thingsboard_uri,
        framerate=parameters.microphone_framerate,
        send_text_callback=bot.send_text,
    )
    bot.start(recorder)


if __name__ == "__main__":
    main()
