import pathlib

import matplotlib.pyplot as plt

from dog_bark.bark import Bark


def plot_bark(bark: Bark, to_file: bool = False) -> None:
    plt.style.use("seaborn-colorblind")
    fig, ax = plt.subplots()
    ax.plot(bark.times, bark.amplitude_envelope)
    ax.set_title("Bark times")
    ax.set_ylabel("Amplitude")
    ax.set_xlabel("Time (s)")

    if not to_file:
        plt.show()
    file = pathlib.Path(bark.file_name)
    out_file = file.with_suffix(".png")
    fig.savefig(str(out_file))
