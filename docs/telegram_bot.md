# Telegram bot

> The telegram bot will not be maintained in the long run.
> Use the [Matrix bot](matrix_bot.md) instead.

## Create

create a [Telegram bot](https://www.rowy.io/blog/create-telegram-bot) and obtain the api key to input in the [config file](record.md).

## Use

To see all commands available to the bot, send `\help` to your bot.

Example of commands available to the bot are:

* `\register`: register to receive updates from the bot.
* `\start`: start the recorder
* `\stop`: stop the recorder
* `\status`: get the current status of the recorder -> is it recording and how long as the animal barked today.
* `\pause`: pause the current recording without stopping it---on/off time won't be registered in the app state.
* `\unpause`: restart a paused recorder.
* `\bark_level`: return the threshold for amplitude if using the amplitude based detection.

See in the file `bark_monitor/very_bark_bot.py` to see the commands available to the bot.
