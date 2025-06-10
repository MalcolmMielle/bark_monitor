from contextlib import asynccontextmanager
from typing import Any

import tyro
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from bark_monitor import logger
from bark_monitor.cli.get_param import Parameters
from bark_monitor.next_cloud_sync import NextCloudSync
from bark_monitor.recorders.recording import Recording
from bark_monitor.recorders.yamnet_recorder import YamnetRecorder

recoder: dict[str, YamnetRecorder] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.warning(
        "\n\n\n/*************\nIMPORTANT: If using the snap make sure to plug all the"
        " available slots with "
        "`sudo snap connect bark-monitor:XXX`.\n"
        "See available slots with `snap connections bark-monitor`\n/*************\n\n\n"
    )

    parameters = tyro.cli(Parameters)

    sync_service = NextCloudSync(
        server="SERVER",
        user="USERNAME",
        passwd="PASSWORD",
    )

    recoder["yamnet"] = YamnetRecorder(
        sync=sync_service,
        output_folder=parameters.output_folder,
        sampling_time_bark_seconds=parameters.sampling_time_bark_seconds,
        http_url=parameters.thingsboard_uri,
        framerate=parameters.microphone_framerate,
    )

    yield


def main():
    app = FastAPI(lifespan=lifespan)

    @app.post("/start")
    async def start() -> dict[str, str]:
        recoder["yamnet"].record()
        return {"result": "Started the recording"}

    @app.post("/stop")
    async def stop() -> dict[str, str]:
        recoder["yamnet"].stop()
        return {"result": "Stopped the recording"}

    @app.get("/status")
    async def status() -> dict[str, Any]:
        is_running = recoder["yamnet"].running
        return {"result": is_running}

    @app.get("/activity")
    async def activity() -> dict[str, Any]:
        recording = Recording.read(
            output_folder=recoder["yamnet"].output_folder,
            sync_service=recoder["yamnet"].sync,
        )
        activities = recording.daily_activities_formated()
        return {"activities": activities}

    @app.get("/last_audio")
    async def last_audio() -> FileResponse:
        audio_folder = recoder["yamnet"].today_audio_folder
        audio_files = audio_folder.glob("*")
        if len(list(audio_files)) == 0:
            raise HTTPException(status_code=404, detail="No audio files found")
        audio_file = max(audio_files, key=lambda p: p.stat().st_ctime)
        return FileResponse(audio_file)

    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
