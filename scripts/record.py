import argparse

from bark_monitor.recorders.recorder import Recorder
from bark_monitor.very_bark_bot import VeryBarkBot


def get_parameters() -> bool:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--accept-new-users",
        type=bool,
        help="If true new users will be accepted by the bot",
        default=False,
    )

    args = parser.parse_args()
    return args.accept_new_users


def main():
    accept_new_users = get_parameters()
    threshold = 10_000

    recorder = Recorder(threshold)
    VeryBarkBot(recorder, accept_new_users)


if __name__ == "__main__":
    main()
