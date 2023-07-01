# Install

The bark monitor relies on pyaudio and portaudio.
Start by installing gcc/g++ and portaudio.
On Ubuntu:

```bash
sudo apt install build-essential
sudo apt-get install portaudio19-dev
```

Install with tensorflow for Deep Learning based detection using [Yamnet](https://www.tensorflow.org/hub/tutorials/yamnet):

`pip install .[ml]`

Install without tensorflow to use amplitude based detection:

`pip install .`

Tested with python 3.9, should work with higher versions too.

To run the unit tests and be able to contribute, install the package in editable mode using the `-e` option for pip.
