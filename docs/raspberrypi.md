# Raspberry pi

The bark monitor was tested on Raspberry pi 4, running Ubuntu 24.05 and python 3.12.
I used a 2G raspberry pi but needed to [add 2Gb swap file](https://www.digitalocean.com/community/tutorials/how-to-add-swap-space-on-ubuntu-20-04) to use the Yamnet model (might be unecessary for the lite model).

## Set up microphone

Since the raspberry pi 4 has no microphone, I have used [Adafruit mini USB microphone](https://www.adafruit.com/product/3367).

Make sure you are part of the audio group.

`usermod -aG audio <user>`

If you are not part of the group you might have this weird error where you cannot access audio device when not logged in the locally on the machine.

E.g. connected as ssh, `aplay -l` return  `aplay: device_list:268: no soundcards found...`, _but_, if you are logged in locally on the machine, _then_ `apply -l` from the ssh terminal returns:

```bash
**** *List of PLAYBACK Hardware Devices* ****
card 0: Intel [HDA Intel], device 0: ALC662 rev1 Analog [ALC662 rev1 Analog]
  Subdevices: 1/1
  Subdevice #0: subdevice #0
card 1: HDMI [HDA ATI HDMI], device 3: HDMI 0 [HDMI 0]
  Subdevices: 1/1
  Subdevice #0: subdevice #0
```
