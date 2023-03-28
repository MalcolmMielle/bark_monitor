from bark_monitor.recorders.recorder import Recorder
from bark_monitor.very_bark_bot import VeryBarkBot


def main():
    threshold = 10_000

    recorder = Recorder(threshold)
    VeryBarkBot(recorder)


if __name__ == "__main__":
    main()
