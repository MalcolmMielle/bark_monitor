from bark_monitor.cli.get_param import get_parameters
from bark_monitor.recorders.yamnet_recorder import YamnetRecorder
from bark_monitor.very_bark_bot import VeryBarkBot


def main():
    (
        accept_new_users,
        api_key,
        output_folder,
        config_folder,
        things_board_device,
        microphone_framerate,
        sampling_time_bark_seconds,
        google_creds,
    ) = get_parameters()

    recorder = YamnetRecorder(
        output_folder=output_folder,
        sampling_time_bark_seconds=sampling_time_bark_seconds,
        http_url=things_board_device,
        framerate=microphone_framerate,
    )
    bot = VeryBarkBot(
        api_key=api_key,
        config_folder=config_folder,
        accept_new_users=accept_new_users,
        google_creds=google_creds,
    )
    recorder.start_bot(bot)


if __name__ == "__main__":
    main()
