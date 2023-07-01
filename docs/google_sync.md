# Sync with google drive

It is possible to save the recordings to google drive automatically although the feature is very experimental.

When used, the config file of dog activities and recording time will be safe and "sync" with your google drive as a json.

On the other hand, audio recordings also will be saved but the code will __erase__ current audio saved on the drive!
There is "merging" ability to save the audio since they are simply uploaded as a zip folder.
Contribution to make this system better are welcomed but it works for me so I won't change it myself :).

## Set up credentials

To enable the bark_monitor to save to your google drive, follow this [tutorial](https://developers.google.com/drive/api/quickstart/python) to enable the Google API and configure the OAuth consent screen of your app.
At the end of the process you should get a `credentials.json`.
Add the path to the credentials file in the [config](record.md#set-up-the-configuration-file) for the key:

```json
"google credentials": "clients_secrets.json"
```

You can now send `/login` to the bot to connect to your google drive account and enable automatic saves.
