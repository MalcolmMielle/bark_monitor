# Nextcloud

Nextcloud sync is the recommanded way to sync and save your data.

Add the following parameters in you configuration json file:

```json
"nextcloud_parameters": {
    "py/object": "bark_monitor.cli.get_param.NextCloudParameters",
    "server": "https://server.url",
    "user": "userName",
    "passwd": "password"
},
```

And sync should be automatically enabled.

> Be carfeul that, audio recordings also will be saved but the code will __erase__ current audio saved on the drive!
> There is no "merging" ability to save the audio since they are simply uploaded as a zip folder.
> So make sure to save previous audio file if you start a new bark monitor from scratch or the previuos recordings will be erased.
