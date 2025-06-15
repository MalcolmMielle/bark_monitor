from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi_rss import (
    RSSFeed,
    RSSResponse,
)

from bark_monitor.recorders.base_recorder import BaseRecorder
from bark_monitor.recorders.recording import Recording


def fasdtapi_webver(recorder: BaseRecorder) -> FastAPI:
    app = FastAPI()

    @app.post("/start")
    async def start() -> dict[str, str]:
        recorder.record()
        return {"result": "Started the recording"}

    @app.post("/stop")
    async def stop() -> dict[str, str]:
        recorder.stop()
        return {"result": "Stopped the recording"}

    @app.get("/status")
    async def status() -> dict[str, Any]:
        is_running = recorder.running
        return {"result": is_running}

    @app.get("/daily_activities")
    async def daily_activities() -> dict[str, Any]:
        recording = Recording.read(
            output_folder=recorder.output_folder,
            sync_service=recorder.sync,
        )
        activities = recording.daily_activities_formated()
        return {"activities": activities}

    @app.get("/activities")
    async def activities() -> dict[str, Any]:
        recording = Recording.read(
            output_folder=recorder.output_folder,
            sync_service=recorder.sync,
        )
        activities = recording.activities_formated()
        return {"activities": activities}

    @app.get("/last_audio")
    async def last_audio() -> FileResponse:
        audio_folder = recorder.today_audio_folder
        audio_files = audio_folder.glob("*")
        if len(list(audio_files)) == 0:
            raise HTTPException(status_code=404, detail="No audio files found")
        audio_file = max(audio_files, key=lambda p: p.stat().st_ctime)
        return FileResponse(audio_file)

    @app.get("/time_barked")
    async def time_barked() -> dict[str, int]:
        recording = Recording.read(
            output_folder=recorder.output_folder,
            sync_service=recorder.sync,
        )
        return {"time barked": recording.time_barked.seconds}

    @app.get("/rss")
    async def root():
        recording = Recording.read(
            output_folder=recorder.output_folder,
            sync_service=recorder.sync,
        )
        feed = RSSFeed(**(recording.feed_data))
        return RSSResponse(feed)

    return app
