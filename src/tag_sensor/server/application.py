from __future__ import annotations

from contextlib import asynccontextmanager, AsyncExitStack
import os
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import (  # StreamingResponse,
    HTMLResponse,
    RedirectResponse,
    Response,
)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import structlog

from tag_sensor.frame import Frame
from tag_sensor.manager import Manager as ManagerType

from .dependencies import Camera, Cameras, Manager, Marker, Markers, app_context
from .metrics import instrumentator, setup_metrics
from .mqtt import MQTTHelper
from .utils import shutting_down

logger = structlog.get_logger()

DIR = Path(__file__).parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    manager = ManagerType()
    manager.load_config(os.environ["TAG_SENSOR_CONFIG"])

    setup_metrics(app, manager)

    shutting_down.clear()

    async with AsyncExitStack() as stack:
        mqtt = await stack.enter_async_context(MQTTHelper(manager))

        await manager.start()
        yield {"manager": manager, "mqtt": mqtt}
        shutting_down.set()
        await manager.stop()


app = FastAPI(lifespan=lifespan)
instrumentator.instrument(app)
app.mount("/static", StaticFiles(directory=DIR / "static"), name="static")

templates = Jinja2Templates(
    directory=DIR / "templates",
    context_processors=[app_context],
)
TemplateResponse = templates.TemplateResponse


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return TemplateResponse(
        request=request,
        name="index.html",
        context={"request": request},
    )


@app.get("/marker/{marker_id}")
async def get_marker_page(request: Request, marker: Marker):
    return TemplateResponse(
        request=request,
        name="marker.html",
        context={"request": request, "marker": marker},
    )


@app.get("/camera/{camera_id}")
async def get_camera_page(request: Request, camera: Camera):
    return TemplateResponse(
        request=request,
        name="camera.html",
        context={"request": request, "camera": camera},
    )


@app.get("/camera/{camera_id}/calibrate")
async def start_camera_calibration(
    camera: Camera,
    manager: Manager,
    background_tasks: BackgroundTasks,
):
    calibrator = manager.get_calibrator(camera)
    background_tasks.add_task(calibrator.calibrate)
    return RedirectResponse(f"/camera/{camera.config.id}")


def is_empty(data: Any):
    if isinstance(data, dict):
        return all(is_empty(v) for v in data.values())
    if isinstance(data, list):
        return all(is_empty(v) for v in data)
    return data is None


def scrub(data: Any):
    if isinstance(data, BaseModel):
        return scrub(data.model_dump())
    if isinstance(data, dict):
        return {k: scrub(v) for k, v in data.items() if not is_empty(v)}
    if isinstance(data, list):
        return [scrub(v) for v in data]
    if isinstance(data, str):
        return data
    return data


@app.get("/api/markers")
async def list_markers(markers: Markers):
    return scrub([marker.config for marker in markers])


@app.get("/api/cameras")
async def list_cameras(cameras: Cameras):
    return scrub([camera.config for camera in cameras])


@app.get("/api/marker/{marker_id}")
async def get_marker(marker: Marker):
    return scrub(marker.config)


@app.get("/api/camera/{camera_id}")
async def get_camera(camera: Camera):
    return scrub(camera.config)


@app.get("/api/detections")
async def get_all_detections(manager: Manager):
    return manager.detections


@app.get(
    "/marker/{marker_id}/{which}.png",
    responses={200: {"content": {"image/png": {}}}},
    response_class=Response,
)
async def get_marker_image(
    marker: Marker,
    which: Literal["original", "annotated"],
):
    return image_from(marker, which)


@app.get(
    "/camera/{camera_id}/{which}.png",
    responses={200: {"content": {"image/png": {}}}},
    response_class=Response,
)
async def get_camera_image(
    camera: Camera,
    which: Literal["original", "annotated"],
):
    return image_from(camera, which)


def image_from(
    source: Any,
    which: Literal["original", "annotated"],
):
    frame = getattr(source, f"{which}_frame", None)
    if not isinstance(frame, Frame):
        return Response(status_code=404)
    return Response(content=frame.to_png(), media_type="image/png")
