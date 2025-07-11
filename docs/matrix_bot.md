# Matrix bot

Matrix is a decentralyze messaging app.
It can be used to control the bark monitor.
The bot is bot is based on [nio-bot](https://docs.nio-bot.dev/master/)

Follow the [get started](https://docs.nio-bot.dev/master/guides/001-getting-started/) tutorial of nio-bot and do not forget to install `libolm` and `libmagic`.
To work the matrix bot needs your homeserver, user name, and password.
Sadly, it doesn't seem to work with the access token.

An example of the Matrix bot section in the parameters would look like this:

```json
"matrix_parameters": {
    "py/object": "bark_monitor.cli.get_param.MatrixParameters",
    "homeserver": "https://homeserver.org",
    "user_id": "user_id", // Without the @ and the homeserver after
    "password": "PASSWORD"
},
```

The matrix bot and the bark monitor can be started with `python bark_monitor/cli/matrix/yamnet_record.py --config-file path_to_config_file.json` or by typing the command with the arguments.

Then by starting a conversation with the `user_id` (don't forget to accept the request on `user_id`'s side), you can get use the matrix bot.

