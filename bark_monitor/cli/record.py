import argparse
import json

from bark_monitor.recorders.recorder import Recorder


def get_parameters() -> tuple[bool, str, str, str]:
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
    return (
        args.accept_new_users,
        json_data["api_key"],
        json_data["output_folder"],
        json_data["config_folder"],
    )


def main():
    accept_new_users, api_key, output_folder, config_folder = get_parameters()

    recorder = Recorder(api_key, config_folder, output_folder, accept_new_users)
    recorder.start_bot()


if __name__ == "__main__":
    main()
