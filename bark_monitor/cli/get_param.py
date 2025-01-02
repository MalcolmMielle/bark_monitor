import argparse
import json

from bark_monitor import logger


def get_parameters() -> tuple[bool, str, str, str, str | None, int, int, str | None]:
    logger.warning(
        "\n\n\n/*************\nIMPORTANT: If using the snap make sure to plug all the"
        " available slots with "
        "`sudo snap connect bark-monitor:XXX`.\n"
        "See available slots with `snap connections bark-monitor`\n/*************\n\n\n"
    )

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

    microphone_framerate = (
        json_data["microphone framerate"]
        if "microphone framerate" in json_data
        else 16000
    )

    sampling_time_bark_seconds = (
        json_data["sampling time bark seconds"]
        if "sampling time bark seconds" in json_data
        else 1
    )

    google_cred = (
        json_data["google credentials"] if "google credentials" in json_data else None
    )

    return (
        args.accept_new_users,
        json_data["api_key"],
        json_data["output_folder"],
        json_data["config_folder"],
        things_board_url,
        microphone_framerate,
        sampling_time_bark_seconds,
        google_cred,
    )
