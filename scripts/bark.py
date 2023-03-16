import argparse

from bark_monitor.bark import Bark
from bark_monitor.plot.plot_bark import plot_bark


def main():
    parser = argparse.ArgumentParser(
        description="Process a file and plot to see if barks."
    )
    parser.add_argument(
        "--filename",
        type=str,
        help="the file to analyse",
        default="recordings/14mars_night.wav",
    )
    parser.add_argument("--step", type=int, help="step to sample audio", default=100)
    args = parser.parse_args()

    bark = Bark(args.filename, args.step)

    print(bark)
    plot_bark(bark)


if __name__ == "__main__":
    main()
