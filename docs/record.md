# Record your dog

Once you have [installed](install.md) the program and created a [telegram bot](telegram_bot.md), you can start recording and monitor your dog.

## Set up the configuration file

The bark monitor will read the configuration from a json file.
By default, it will read the file `config.json` but use the option `config-file` to point to any path.

The config file should look like this at minimum:

```json
{
  "api_key": "you api key to the telegram bot",
  "output_folder": "where to save the recordings",
  "config_folder": "where to save the telegram bot configuration"
}

```

More options are available in the recorder's programs found in `bark_monitor/cli`.

## Register users

If it is your first time launching the bark monitor, the first step is to register your user.
Users can only be registered if the monitor is launched in register mode: `bark-monitor --accept-new-users`.
Once the monitor is launched, open your telegram bot, and send `/register`.
You should now be register to this machine, and able receive notifications and control it.

## Launch the recordings

Launching the bark monitor is as simple as entering `bark-monitor --config-file <path to config file>`.
If the set-up is correct you should receive a notification when the monitor is ready the record.
To start a recording send `/start` to the bot.
To stop it send `/stop`.
See the [telegram bot documentation](telegram_bot.md) for more details on what the bot can do.

If you are on Raspberry Pi or other device, consider using the [TFlite version of Yamnet](https://tfhub.dev/google/lite-model/yamnet/classification/tflite/1) by using `bark-monitor-lite --config-file <path to config file>` instead.
