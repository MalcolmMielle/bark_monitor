# Record your dog

Once you have [installed](install.md) the program and created a [telegram bot](telegram_bot.md), you can start recording and monitor your dog.

## Set up the configuration file

The bark monitor will read the configuration from a json file.
By default, it will read the file `config.json` but use the option `config-file` to point to any path.

The config file should look like this:

```json
{
    "py/object": "bark_monitor.cli.get_param.Parameters",
    "output_folder": {
        "py/reduce": [
            {
                "py/type": "pathlib.PosixPath"
            },
            {
                "py/tuple": [
                    "outputs"
                ]
            }
        ]
    },
    "config_folder": {
        "py/reduce": [
            {
                "py/type": "pathlib.PosixPath"
            },
            {
                "py/tuple": [
                    "config"
                ]
            }
        ]
    },
    "api_key": null,
    "config_file": null,
    "microphone_framerate": 16000,
    "sampling_time_bark_seconds": 1,
    "accept_new_users": false,
    "google_creds": null,
    "matrix_parameters": {
        "py/object": "bark_monitor.cli.get_param.MatrixParameters",
        "homeserver": "https://HOMESERVER",
        "user_id": "USER_ID",
        "password": "PASSWORD"
    },
    "nextcloud_parameters": {
        "py/object": "bark_monitor.cli.get_param.NextCloudParameters",
        "server": "https://SERVER.URL",
        "user": "USERNAME",
        "passwd": "PASSWORD"
    },
    "thingsboard_parameters": null
}
```

> The json has the `py/object` attributes because it is a jsonpickle export.

## Register users

If it is your first time launching the bark monitor, the first step is to register your user.
Users can only be registered if the monitor is launched in register mode: `bark-monitor --accept-new-users`.
Once the monitor is launched, open your telegram bot, and send `/register`.
You should now be register to this machine, and able receive notifications and control it.

## Launch the recordings

Launching the bark monitor is as simple as entering `bark-monitor --config-file <path to config file>`.

> As of now, `bark-monitor --config-file <path to config file>` launches the telegram bot.
> However, the matrix bot is recommanded and how to launch it is shown in [its documentation](matrix_bot.md).

If the set-up is correct you should receive a notification when the monitor is ready the record.
To start a recording send `/start` to the bot.
To stop it send `/stop`.
See the [matrix](matrix_bot.md) or [telegram bot documentation](telegram_bot.md) for more details on what the bots can do.

If you are on Raspberry Pi or other device, consider using the [TFlite version of Yamnet](https://tfhub.dev/google/lite-model/yamnet/classification/tflite/1) by using `bark-monitor-lite --config-file <path to config file>` instead.
