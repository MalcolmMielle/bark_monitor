# Bark monitor

[![Get it from the Snap Store](https://snapcraft.io/static/images/badges/en/snap-store-black.svg)](https://snapcraft.io/bark-monitor)

![my dog](images/watson.jpg)

Showing my neighbor my dog doesn't bark!

Get it today: `pip install bark-monitor` or `snap install bark-monitor`.

## Introduction

Do you also have neighbor who accuses your dog of barking all the time, want to kick you out of your flat because of it, even though you know _it's not true_?
Do you want to know if your dog is actually noisy when you are gone but you don't (and don't want to buy) a baby cam?

Then this project is for you!

## How to use the bark monitor

The bark monitor will:

* Record your dog while you are gone.
  The recordings are saved in a folder to enable you to really show that neighbor they are full of shit.
* Monitor its barking real time and send you notification through a Telegram bot when your neighbor drives the dog crazy and they barks.
  Detection of the bark can be done using the [Yamnet](https://www.tensorflow.org/hub/tutorials/yamnet) neural network implemented in tensorflow, or the amplitude of the signal.
  Using Yamnet, cats are also tracked ;).

## Install and use

Check out our [documentation](https://malcolmmielle.codeberg.page/bark_monitor/@pages/) for information on how to [install](https://malcolmmielle.codeberg.page/bark_monitor/@pages/install/), [use](https://malcolmmielle.codeberg.page/bark_monitor/@pages/record/), and more.

## Contributions

Contributions are always welcome to help show my neighbor is wrong!

Code submitted should be formatted with [ruff](https://docs.astral.sh/ruff/) and the code is managed with [uv](https://docs.astral.sh/uv/).
All methods should be type hinted and return types should always be present even when it's `None`.

If possible, submit unit tests and a picture of your dog with your PR (I also accept cat pictures as payments).
