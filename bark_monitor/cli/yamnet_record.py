import argparse
import json
from typing import Optional

from bark_monitor.recorders.yamnet_recorder import YamnetRecorder


def get_parameters() -> tuple[bool, str, str, str, Optional[str]]:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config-file",
        type=str,
        help="Path to config file",
        default="config.json",
    )
    parser.add_argument(
        "--accept-new-users",
        action=argparse.BooleanOptionalAction,
        help="If true new users will be accepted by the bot",
    )

    args = parser.parse_args()
    with open(args.config_file, "rb") as f:
        json_data = json.load(f)

    things_board_url = None
    if (
        "thingsboard_ip" in json_data
        and "thingsboard_port" in json_data
        and "thingsboard_device_token" in json_data
    ):
        things_board_url = (
            "http://"
            + json_data["thingsboard_ip"]
            + ":"
            + str(json_data["thingsboard_port"])
            + "/api/v1/"
            + json_data["thingsboard_device_token"]
            + "/telemetry"
        )
    return (
        args.accept_new_users,
        json_data["api_key"],
        json_data["output_folder"],
        json_data["config_folder"],
        things_board_url,
    )


def main():
    (
        accept_new_users,
        api_key,
        output_folder,
        config_folder,
        things_board_device,
    ) = get_parameters()

    recorder = YamnetRecorder(
        api_key=api_key,
        config_folder=config_folder,
        output_folder=output_folder,
        accept_new_users=accept_new_users,
        sampling_time_bark_seconds=1,
        http_url=things_board_device,
    )
    recorder.start_bot()


if __name__ == "__main__":
    main()
