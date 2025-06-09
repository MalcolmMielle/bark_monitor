import tyro

from bark_monitor import logger
from bark_monitor.cli.get_param import Parameters
from bark_monitor.google_sync import GoogleSync
from bark_monitor.recorders.recorder import Recorder
from bark_monitor.very_bark_bot import VeryBarkBot


def main():
    logger.warning(
        "\n\n\n/*************\nIMPORTANT: If using the snap make sure to plug all the"
        " available slots with "
        "`sudo snap connect bark-monitor:XXX`.\n"
        "See available slots with `snap connections bark-monitor`\n/*************\n\n\n"
    )

    parameters = tyro.cli(Parameters)

    sync_service = GoogleSync(credential_file=parameters.google_creds)

    recorder = Recorder(sync=sync_service, output_folder=parameters.output_folder)
    bot = VeryBarkBot(
        api_key=parameters.api_key,
        config_folder=parameters.config_folder,
        accept_new_users=parameters.accept_new_users,
        sync=sync_service,
    )
    recorder.start_bot(bot)


if __name__ == "__main__":
    main()
