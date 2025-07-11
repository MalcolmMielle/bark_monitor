# Install

## Snap

[![Get it from the Snap Store](https://snapcraft.io/static/images/badges/en/snap-store-black.svg)](https://snapcraft.io/bark-monitor)

When using the snape make sure to plug all the connection or the microphone won't be found.
List all connections with:

```bash
snap connections bark-monitor
```

connect them with:

```bash
sudo snap connect bark-monitor:XXX
```

This should connect them all:

```bash
sudo snap connect bark-monitor:alsa
sudo snap connect bark-monitor:pulseaudio
sudo snap connect bark-monitor:audio-record
```

## Pypi

Get from pypi with `pip install bark-monitor`.

## Manual install

The bark monitor relies on pyaudio and portaudio.
Start by installing gcc/g++ and portaudio.
On Ubuntu:

```bash
sudo apt install build-essential
sudo apt install portaudio19-dev
sudo apt install libolm-dev
```

Install using [UV](https://docs.astral.sh/uv/) on python 3.12.
Run in the root folder:

```bash
uv sync
```
