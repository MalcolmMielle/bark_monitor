# Install

[![Get it from the Snap Store](https://snapcraft.io/static/images/badges/en/snap-store-black.svg)](https://snapcraft.io/bark-monitor)

Get from pipy with `pip install bark-monitor`.

## Manual install

The bark monitor relies on pyaudio and portaudio.
Start by installing gcc/g++ and portaudio.
On Ubuntu:

```bash
sudo apt install build-essential
sudo apt-get install portaudio19-dev
```

Install using [UV](https://docs.astral.sh/uv/) on python 3.12.
Run in the root folder:

```bash
uv sync
```
