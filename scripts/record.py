from datetime import datetime
from pathlib import Path

from dog_bark.bark import Bark
from dog_bark.plot.plot_bark import plot_bark
from dog_bark.recorder import Recorder


def main():
    threshold = 100

    now = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
    filepath = Path("recordings", now + ".wav")
    with Recorder(str(filepath), bark_level=threshold) as rec:
        rec.record()

    bark = Bark(str(filepath), threshold=threshold)
    print(bark)
    plot_bark(bark, to_file=True)


if __name__ == "__main__":
    main()
