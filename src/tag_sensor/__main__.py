from __future__ import annotations

from asyncio import sleep
from pathlib import Path
from subprocess import run as _subprocess_run  # nosec
from types import SimpleNamespace
from typing import TYPE_CHECKING, Annotated, Any, Optional

from click import pass_context
from rich.pretty import pprint
from typer import Argument, Context, Option

from .camera import CameraNotFoundError
from .cli_utils import App, Format, format_output
from .emitter import add_event_listener
from .family import FamilyNotFoundError, get_family, is_family_group
from .manager import Manager
from .marker import Marker, MarkerConfig, MarkerNotFoundError
from .renderer import MarkerPNG, MarkerSTL, MarkerSVG, render_text
from .utils import NotFoundError

# pylint: disable=redefined-outer-name

if TYPE_CHECKING:
    from .detection import Detection
    from .frame import Frame

app = App()


@pass_context  # type: ignore
def handle_result(ctx: Context, result: Any, **_):
    format_output(ctx.obj.output, result)


@app.callback(result_callback=handle_result)
async def main_callback(
    ctx: Context,
    output: Annotated[
        Format,
        Option(
            help="Set the output format",
            envvar="CLI_FORMAT",
            case_sensitive=False,
        ),
    ] = Format.PRETTY,
    config_file: Annotated[
        str,
        Option("--config", envvar="TAG_SENSOR_CONFIG"),
    ] = "./config.yaml",
):
    """Tag Sensor Management Tool."""

    manager = Manager()
    manager.load_config(config_file)

    def get_markers(
        ids: Optional[list[str]] = None,
        family: str = "4X4",
    ):
        if not is_family_group(family):
            raise FamilyNotFoundError(family)

        if ids:
            for _id in parse_ids(ids):
                marker = manager.get_marker(_id)
                if marker:
                    yield marker
                elif isinstance(_id, int):
                    yield Marker(
                        config=MarkerConfig(
                            id=f"marker-{id}",
                            tag_id=_id,
                            family=family,
                        ),
                    )
                else:
                    raise MarkerNotFoundError(_id)
        else:
            yield from manager.markers

    def do_renders(
        cls: type[MarkerPNG | MarkerSVG | MarkerSTL],
        ids: list[str] | None,
        family: str = "4X4",
        **options,
    ):
        opts = {
            key: value for key, value in options.items() if value is not None
        }
        opts["family"] = get_family(family or "4X4")
        opts["directory"] = Path(opts.get("directory", "."))

        # renderer = cls( **opts )
        for marker in get_markers(ids, family=family):
            cls.make_renderer_for(marker, **opts).render(marker)

    ctx.obj = SimpleNamespace(
        output=output,
        manager=manager,
        get_markers=get_markers,
        do_renders=do_renders,
    )
    await ctx.obj.manager.prepare()


@app.command()
async def config(ctx: Context):
    """Show configuration."""

    return ctx.obj.manager.config


@app.command()
async def cameras(ctx: Context):
    """List cameras."""

    for camera in ctx.obj.manager.cameras:
        print(camera.id)


@app.command()
async def camera(ctx: Context, camera_id: str):
    """Show the configuration and state of a camera."""

    return ctx.obj.manager.camera(camera_id)


@app.command()
async def detections(ctx: Context):
    """List all tags detected by all cameras right now."""

    async for detection in ctx.obj.manager.get_detections():
        if detection.marker is None:
            print(f"#{detection.tag_id}", "-", detection.camera.id)
        else:
            print(detection.marker.config.id, "-", detection.camera.id)


@app.command()
async def markers(ctx: Context):
    """List markers."""

    for marker in ctx.obj.manager.markers:
        print(marker.config.tag_id, marker.config.id)


@app.command()
async def marker(ctx: Context, marker_id: str):
    """Show the configuration and state of a marker."""

    return ctx.obj.manager.marker(marker_id)


@app.command()
async def show_markers(
    ctx: Context,
    ids: Annotated[Optional[list[str]], Argument()] = None,
    family: Annotated[str, Option()] = "4X4",
):
    """
    Show an ASCII representation of a marker.

    If the argument is numeric then it will just show you that
    `tag_id` (in this case you can also specify `--family` to show the
    marker from a different family).

    If the argument is a string then it will be assumed to be the `id`
    of a marker from the configuration, and that marker will be shown.
    """

    for marker in ctx.obj.get_markers(ids, family=family):
        marker.config.label = False
        print(render_text(marker))
        if marker.config.name:
            print(f"{marker.config.tag_id} : {marker.config.name}")
        else:
            print(f"   {marker.config.tag_id}")


def parse_ids(value: str | list[str]):
    if isinstance(value, list):
        for val in value:
            yield from parse_ids(val)
    elif "," in value:
        for val in value.split(","):
            yield from parse_ids(val.strip())
    elif "-" in value:
        start, end = value.split("-")
        yield from range(int(start), int(end) + 1)
    elif value.isnumeric():
        yield int(value)
    else:
        yield value


@app.command()
def make_png_markers(
    ctx: Context,
    ids: Annotated[Optional[list[str]], Argument()] = None,
    family: Annotated[str, Option()] = "4X4",
    directory: Annotated[str, Option()] = ".",
    filename: Annotated[Optional[str], Option()] = None,
    label: Annotated[Optional[str], Option()] = None,
    size: Annotated[Optional[float], Option()] = None,
    dpi: Annotated[Optional[int], Option()] = None,
):
    """Make .png markers."""

    ctx.obj.do_renders(
        MarkerPNG,
        ids,
        family,
        directory=directory,
        filename=filename,
        label=label,
        size=size,
        dpi=dpi,
    )


@app.command()
def make_svg_markers(
    ctx: Context,
    ids: Annotated[Optional[list[str]], Argument()] = None,
    family: Annotated[str, Option()] = "4X4",
    directory: Annotated[Optional[str], Option()] = None,
    filename: Annotated[Optional[str], Option()] = None,
    label: Annotated[Optional[str], Option()] = None,
    size: Annotated[Optional[float], Option()] = None,
):
    """Make .svg markers."""

    ctx.obj.do_renders(
        MarkerSVG,
        ids,
        family,
        directory=directory,
        filename=filename,
        label=label,
        size=size,
    )


@app.command()
def make_stl_markers(
    ctx: Context,
    ids: Annotated[Optional[list[str]], Argument()] = None,
    family: Annotated[str, Option()] = "4X4",
    directory: Annotated[Optional[str], Option()] = None,
    filename: Annotated[Optional[str], Option()] = None,
    label: Annotated[Optional[str], Option()] = None,
    size: Annotated[Optional[float], Option()] = None,
    grid_thickness: Annotated[Optional[float], Option()] = None,
    base_thickness: Annotated[Optional[float], Option()] = None,
    hole_diameter: Annotated[Optional[float], Option()] = None,
    hole_depth: Annotated[Optional[float], Option()] = None,
    hole_offset: Annotated[Optional[float], Option()] = None,
    spacer_height: Annotated[Optional[float], Option()] = None,
    spacer_diameter: Annotated[Optional[float], Option()] = None,
    label_size: Annotated[Optional[float], Option()] = None,
    label_font: Annotated[Optional[str], Option()] = None,
    label_depth: Annotated[Optional[float], Option()] = None,
    drill_guide: Annotated[Optional[bool], Option()] = None,
    scad_only: Annotated[bool, Option()] = False,
    keep_scad: Annotated[bool, Option()] = False,
):
    """Make 3D printable .stl marker files."""

    ctx.obj.do_renders(
        MarkerSTL,
        ids,
        family,
        directory=directory,
        filename=filename,
        label=label,
        size=size,
        grid_thickness=grid_thickness,
        base_thickness=base_thickness,
        hole_diameter=hole_diameter,
        hole_depth=hole_depth,
        hole_offset=hole_offset,
        spacer_height=spacer_height,
        spacer_diameter=spacer_diameter,
        label_size=label_size,
        label_font=label_font,
        label_depth=label_depth,
        drill_guide=drill_guide,
        scad_only=scad_only,
        keep_scad=keep_scad,
    )


@app.command()
async def update_once(
    ctx: Context,
    images: Annotated[bool, Option()] = True,
    attrs: Annotated[bool, Option()] = False,
    updates: Annotated[bool, Option()] = True,
):
    """Update all the sensor instances one time."""

    def _handle(marker: Marker) -> None:
        if updates:
            print("Updating marker:", marker.config.id, marker.is_on)
        if marker.detection:
            if images:
                marker.detection.annotated_frame.display()
            if attrs:
                pprint(marker.detection.attributes)

    manager = ctx.obj.manager
    add_event_listener("marker:updated", _handle)

    await manager.update_detections()


@app.command()
async def make_calibration_board(
    ctx: Context,
    camera_id: str,
    image_format: str = "png",
    output: str = "calibration-board.png",
):  # pragma: no cover
    """Generate a "Charuco" board to use for camera calibration."""

    manager = ctx.obj.manager

    camera = manager.camera(camera_id)
    image = camera.config.calibration.make_calibration_board()
    image.display()
    image.save(output, image_format)


@app.command()
async def calibrate_camera(ctx: Context, camera_id: str):  # pragma: no cover
    """Calibrate a camera."""

    manager = ctx.obj.manager
    camera = manager.camera(camera_id)
    return await manager.get_calibrator(camera).calibrate()


@app.command()
async def get_calibration_images(
    ctx: Context,
    camera_id: str,
    directory: Annotated[str, Option()] = "./calibration-images",
    good: Annotated[Optional[str], Option()] = None,
    bad: Annotated[Optional[str], Option()] = None,
    start: Annotated[Optional[str], Option()] = None,
    done: Annotated[Optional[str], Option()] = None,
):  # pragma: no cover
    """Capture calibration images from a camera."""

    manager = ctx.obj.manager

    def run(cmd: str):
        _subprocess_run(["/bin/sh", "-c", cmd], check=False)  # nosec

    camera = manager.get_camera(camera_id)
    if not camera:
        raise CameraNotFoundError(camera_id)

    def runner(cmd: str):
        def _run():
            run(cmd)

        return _run

    if good:
        add_event_listener("capture:good", runner(good))
    if bad:
        add_event_listener("capture:failed", runner(bad))

    calibrator = manager.get_calibrator(camera)

    if start:
        run(start)
    async for frame in calibrator.capture_frames(save_to=directory):
        yield frame
    if done:
        run(done)


@app.command()
async def detection(
    ctx: Context,
    camera_id: str,
    save_to: Annotated[Optional[str], Option()] = None,
    image_format: str = "png",
    count: Annotated[int, Option()] = 1,
):  # pragma: no cover
    """Capture and annotate a single image from a single camera."""

    manager = ctx.obj.manager
    directory = Path(save_to) if save_to else None

    def handle_frame(name: str, frame: Frame, **__):
        frame.display()
        if directory:
            frame.save(directory / f"{name}", image_format)

    def _handle_detection(detection: Detection):
        pprint(detection)
        handle_frame("detection", detection.annotated_frame)

    def _handle_marker_update(marker: Marker):
        print("Updating marker:", marker.config.id, marker.is_on)

    add_event_listener("detection", _handle_detection)
    add_event_listener("marker:updated", _handle_marker_update)

    camera = manager.camera(camera_id)
    add_event_listener("camera:frame", handle_frame)

    want = count
    while want > 0:
        async for _ in manager.get_detections_for_camera(camera):
            want -= 1
        await sleep(10)


@app.command()
async def get_image(
    ctx: Context,
    camera_id: str,
    file: Annotated[str, Option()] = "./image.png",
    save: Annotated[bool, Option()] = True,
    display: Annotated[bool, Option()] = True,
    # annotate: Annotated[bool, Option()] = True, # TODO
):  # pragma: no cover
    """Capture calibration images from a camera."""

    manager = ctx.obj.manager

    camera = manager.camera(camera_id)
    frame = await manager.get_frame(camera)
    if not frame:
        raise NotFoundError("frame")
    if save:
        frame.save(file)
    if display:
        frame.display()
