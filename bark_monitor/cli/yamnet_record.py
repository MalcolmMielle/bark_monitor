import tyro

from bark_monitor import logger
from bark_monitor.cli.get_param import Parameters
from bark_monitor.google_sync import GoogleSync
from bark_monitor.recorders.yamnet_recorder import YamnetRecorder
from bark_monitor.very_bark_bot import VeryBarkTelegramBot


def main():
    logger.warning(
        "\n\n\n/*************\nIMPORTANT: If using the snap make sure to plug all the"
        " available slots with "
        "`sudo snap connect bark-monitor:XXX`.\n"
        "See available slots with `snap connections bark-monitor`\n/*************\n\n\n"
    )

    parameters = tyro.cli(Parameters)

    sync_service = GoogleSync(credential_file=parameters.google_creds)

    bot = VeryBarkTelegramBot(
        sync=sync_service,
        api_key=parameters.api_key,
        config_folder=parameters.config_folder,
        accept_new_users=parameters.accept_new_users,
    )
    recorder = YamnetRecorder(
        sync=sync_service,
        output_folder=parameters.output_folder,
        sampling_time_bark_seconds=parameters.sampling_time_bark_seconds,
        http_url=parameters.things_board_url,
        framerate=parameters.microphone_framerate,
        send_text_callback=bot.send_text,
    )
    bot.start(recorder)


if __name__ == "__main__":
    main()
