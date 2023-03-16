# Bark monitor

Showing my neighbor my dog doesn't bark.

## Introduction

Do you also have neighbor who accuses your dog of barking all the time, want to kick you out of your flat because of it, even though you know _it's not true_?
Do you want to know if your dog is actually noisy when you are gone but you don't (and don't want to buy) a baby cam?

Then this project is for you!

## How to use the bark monitor

The bark monitor will:

* Record your dog while you are gone.
  The recordings are saved in the `recordings` to really show that neighbor they are full of shit.
* Monitor its barking real time and send you notification through a Telegram bot when your neighbor drives the dog crazy and they barks.

To setup the program:

1. Create a Telegram bot and obtain the api key.
2. Add the api key to a file in the root folder named `api_key`.
3. Start the program by running `scripts/record.py`.

See in the file `bark_monitor/very_bark_bot.py` to see the commands available to the bot.
