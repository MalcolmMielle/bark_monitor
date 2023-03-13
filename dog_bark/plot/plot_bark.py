import pathlib

import matplotlib.pyplot as plt

from dog_bark.bark import Bark


def plot_bark(bark: Bark, to_file: bool = False) -> None:
    plt.style.use("seaborn-colorblind")
    fig, ax = plt.subplots()
    ax.plot(bark.signal_array)
    ax.set_title("Left Channel")
    ax.set_ylabel("Signal Value")
    ax.set_xlabel("Time (s)")

    if not to_file:
        plt.show()
    file = pathlib.Path(bark.file_name)
    out_file = file.with_suffix(".png")
    fig.savefig(str(out_file))
