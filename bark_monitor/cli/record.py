from bark_monitor.cli.get_param import get_parameters
from bark_monitor.recorders.recorder import Recorder
from bark_monitor.very_bark_bot import VeryBarkBot


def main():
    (
        accept_new_users,
        api_key,
        output_folder,
        config_folder,
        _,
        _,
        _,
        google_creds,
    ) = get_parameters()

    recorder = Recorder(output_folder)
    bot = VeryBarkBot(
        api_key=api_key,
        config_folder=config_folder,
        accept_new_users=accept_new_users,
        google_creds=google_creds,
    )
    recorder.start_bot(bot)


if __name__ == "__main__":
    main()
