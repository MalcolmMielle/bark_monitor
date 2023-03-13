import argparse

from dog_bark.bark import Bark
from dog_bark.plot.plot_bark import plot_bark


def main():
    parser = argparse.ArgumentParser(
        description="Process a file and plot to see if barks."
    )
    parser.add_argument(
        "--filename", type=str, help="the file to analyse", default="sounds/13mars.wav"
    )
    parser.add_argument("--step", type=int, help="step to sample audio", default=100)
    args = parser.parse_args()

    bark = Bark(args.filename, args.step)
    plot_bark(bark)


if __name__ == "__main__":
    main()
