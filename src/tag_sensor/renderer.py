from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from string import Template
from typing import TYPE_CHECKING, Any

import cv2
from cv2 import aruco
import numpy
import solid2

from .family import Family
from .model import Model

if TYPE_CHECKING:
    from .marker import Marker

# TODO - Figure out the right type for this
Solid = Any


@dataclass
class Block:
    row: int
    col: int
    size: float
    is_black: bool

    @property
    def color(self):  # pragma: no cover
        return "black" if self.is_black else "white"

    @property
    def x(self):
        return self.col * self.size

    @property
    def y(self):
        return self.row * self.size


class MarkerRendererConfig(Model):
    filename: str = "marker-$tag_id"
    label: str | bool = True
    size: float = 25
    directory: Path = Path()

    @classmethod
    def renderer(cls):
        return cls.__name__.removesuffix("Config")

    @classmethod
    def renderer_class(cls):
        return globals()[cls.renderer()]

    @classmethod
    def format_name(cls):
        return cls.renderer().removeprefix("Marker")

    @classmethod
    def config_name(cls):
        return f"{cls.format_name().lower()}_rendering"


class MarkerRenderer(MarkerRendererConfig):
    family: Family

    @classmethod
    def get_config_options_from(cls, marker: Marker):
        options = {}
        for key in ("rendering", cls.config_name()):
            if o := getattr(marker.config, key, None):
                options.update(o.model_dump())
        return options

    @classmethod
    def make_renderer_for(cls, marker: Marker, **kwargs):
        options = cls.get_config_options_from(marker)
        options.update(kwargs)
        return cls(**options)

    def get_filename(self, marker: Marker) -> Path:
        """Get the filename for a marker, interpreting any template."""
        tmpl = marker.config.filename or self.filename
        return self.directory / self.fill_template(marker, tmpl)

    def get_label(self, marker: Marker) -> str | None:
        """Get the label for a marker, interpreting any template."""
        label = marker.config.label
        if label is None:
            label = self.label
        if label is False:
            return None
        if label is True:
            label = "$tag_id : $name"
        return self.fill_template(marker, label)

    def fill_template(self, marker: Marker, template: str) -> str:
        """Fill a string template with values from the marker."""
        tmpl = Template(template)
        return tmpl.substitute(marker.config.model_dump())

    @cached_property
    def rc(self):
        """Number of rows and columns in the grid."""
        return int(self.family.grid_size)

    @cached_property
    def total_size(self):
        """
        The total size of the marker.

        This includes the grid, and both the black border and white
        quiet area.
        """
        return self.size * (self.rc + 4)

    def get_grid(self, marker: Marker):
        """
        Produce a grid for the given marker.

        Produces a list of lists of booleans, where True means a black
        square and False means a white square.
        """
        # This size is the number of rows and columns in the grid,
        # including the black margin, but not including the white
        # quiet area that surrounds it.
        size = self.rc + 2

        # Make an empty image to render the marker into.
        image = numpy.zeros((size, size, 1), dtype="uint8")
        # Render the marker to give us something to extract the data
        # from.
        aruco.generateImageMarker(
            marker.dictionary,
            marker.config.tag_id,
            size,
            image,
        )

        # Determine how many rows and columns are in the result
        rows, cols, _ = image.shape

        # Transform the grid of pixel values into a grid of booleans
        grid = [
            [bool(image[r, c] == 0) for c in range(cols)] for r in range(rows)
        ]

        # Increase the size by 2, as we're going to add the quiet area
        # around the black outline.
        size += 2
        # Add a new white square to both ends of each row
        grid = [[False, *row, False] for row in grid]
        # Then add an entirely white row to the top and bottom of the grid
        grid = [[False] * size, *grid, [False] * size]

        # Flip the grid... I'm not sure why this is needed but it is.
        return [row[::-1] for row in grid]

    def get_blocks(self, marker: Marker):
        grid = self.get_grid(marker)
        for row, cols in enumerate(grid):
            for col, is_black in enumerate(cols):
                yield Block(row, col, self.size, is_black)


class MarkerPNGConfig(MarkerRendererConfig):
    dpi: int = 72


class MarkerPNG(MarkerRenderer, MarkerPNGConfig):
    def render(self, marker: Marker):
        filename = self.get_filename(marker).with_suffix(".png")
        image = aruco.generateImageMarker(
            marker.dictionary,
            marker.tag_id,
            int(self.total_size * self.dpi),
        )
        cv2.imwrite(str(filename), image)
        return filename


class MarkerSTLConfig(MarkerRendererConfig):
    grid_thickness: float = 5.0
    base_thickness: float = 1.0

    hole_diameter: float = 0
    hole_depth: float = 0
    hole_offset: float = 10

    spacer_height: float = 0
    spacer_diameter: float = 20

    label_size: float = 0.75
    """Label size (as a percentage of the total marker size)."""

    label_font: str = "Helvetica:style=Bold"
    label_depth: float = 0

    drill_guide: bool = True
    scad_only: bool = False
    keep_scad: bool = False


class MarkerSTL(MarkerRenderer, MarkerSTLConfig):
    def render_model(self, marker: Marker):
        blocks = list(self.get_blocks(marker))
        white = self.render_white_core(blocks)
        black = self.render_black_core(blocks)

        if self.spacer_height:
            black = black.translate(0, 0, self.spacer_height)
            white = white.translate(0, 0, self.spacer_height)
            white += self.render_spacers()

        if label := self.render_label(marker):
            pos = self.spacer_height
            if self.label_depth > 0:
                pos -= 0.01
                white -= solid2.translate(0, 0, pos)(label)
            if self.label_depth < 0:
                pos += self.label_depth
                white += solid2.translate(0, 0, pos)(label)

        if self.hole_depth:
            holes = self.render_holes()
            black -= holes
            white -= holes

        return white, black

    def render(self, marker: Marker):
        white, black = self.render_model(marker)

        filename = self.get_filename(marker)

        def save_part(suffix: str, part: Solid):
            name = str(filename)
            if suffix:
                name += f".{suffix}"
            if self.keep_scad and self.scad_only:
                part.save_as_scad(f"{name}.scad")
                return
            part.save_as_stl(f"{name}.stl")
            if self.keep_scad:
                Path(f"{name}.stl.scad").rename(f"{name}.scad")
            else:
                Path(f"{name}.stl.scad").unlink()

        combined = solid2.color("white")(white) + solid2.color("black")(black)

        save_part("", combined)
        save_part("white", white)
        save_part("black", black)

        if self.drill_guide:
            save_part("guide", self.render_drill_guide())

    def render_label(self, marker: Marker):
        if self.label_depth == 0:
            return None  # pragma: no cover
        msg = self.get_label(marker)
        if not msg:
            return None  # pragma: no cover

        mid = self.total_size / 2

        label = solid2.text(
            msg,
            halign="center",
            valign="center",
            font=self.label_font,
            size=10,
        )
        label = solid2.resize(
            self.total_size * self.label_size,
            0,
            0,
            auto=True,
        )(label)
        label = solid2.mirror(1, 0, 0)(label)
        height = abs(self.label_depth)
        label = solid2.linear_extrude(height=height)(label)
        return solid2.translate(mid, mid, 0)(label)

    def render_grid(self, which: bool, blocks: list[Block]):
        return solid2.union()(
            *(
                solid2.cube(
                    b.size,
                    b.size,
                    self.grid_thickness,
                ).translate(b.x, b.y, 0)
                for b in blocks
                if b.is_black == which
            ),
        ).translate(0, 0, self.base_thickness)

    def render_black_core(self, blocks: list[Block]):
        return self.render_grid(True, blocks)

    def render_white_core(self, blocks: list[Block]):
        base = solid2.cube(
            self.total_size,
            self.total_size,
            self.base_thickness,
        )
        bits = self.render_grid(False, blocks)
        return base + bits

    @property
    def hole_centers(self):
        ho = self.hole_offset
        ts = self.total_size
        return [
            [ho, ho],
            [ts - ho, ho],
            [ts - ho, ts - ho],
            [ho, ts - ho],
        ]

    def render_spacers(self):
        h = self.spacer_height
        r = self.spacer_diameter / 2
        return solid2.union()(
            *(
                solid2.cylinder(h=h, r=r).translate(x, y, 0)
                for x, y in self.hole_centers
            ),
        )

    def render_holes(self):
        return solid2.union()(
            *(
                solid2.cylinder(
                    h=self.hole_depth + 0.1,
                    r=self.hole_diameter / 2,
                ).translate(x, y, 0 - 0.1)
                for x, y in self.hole_centers
            ),
        )

    def render_drill_guide(self):
        guide = solid2.cube(
            self.total_size,
            self.total_size,
            self.base_thickness,
        )

        if self.spacer_height:
            h = self.spacer_height + self.base_thickness
            r = self.spacer_diameter / 2
            guide += solid2.union()(
                *(
                    solid2.cylinder(h=h, r=r).translate(x, y, 0)
                    for x, y in self.hole_centers
                ),
            )
        else:
            h = self.base_thickness
            r = self.hole_diameter

        guide -= solid2.union()(
            *(
                solid2.cylinder(
                    h=h + 2,
                    r=self.hole_diameter / 2,
                ).translate(x, y, 0 - 1)
                for x, y in self.hole_centers
            ),
        )

        guide -= solid2.cube(
            self.total_size - (r * 4),
            self.total_size - (r * 4),
            self.base_thickness + 2,
        ).translate(r * 2, r * 2, 0 - 1)
        return guide


class MarkerTXT(MarkerRenderer):
    chars: tuple[str, str] = ("▓", "░")

    def render(self, marker: Marker) -> str:
        grid = self.get_grid(marker)
        text = "\n".join(
            "".join(self.chars[int(x)] for x in row) for row in grid
        )
        label = self.get_label(marker)
        if label:
            text += "\n" + label
        return text


class MarkerSVGConfig(MarkerRendererConfig):
    pass


class MarkerSVG(MarkerRenderer, MarkerSVGConfig):
    def render(self, marker: Marker):
        svg: list[str] = []

        def _mktag(
            key: str,
            opening: bool = False,
            closing: bool = False,
            **kwargs,
        ):
            if closing:
                return f"</{key}>"
            _args = " ".join(f'{k}="{v}"' for k, v in kwargs.items())
            if opening:
                return f"<{key} {_args}>"
            return f"<{key} {_args}/>"

        def tag(key: str, **kwargs):
            svg.append(_mktag(key, **kwargs))

        tag(
            "svg",
            opening=True,
            xmlns="http://www.w3.org/2000/svg",
            width=self.total_size,
            height=self.total_size,
            style="fill:none;",
        )
        for r, row in enumerate(self.get_grid(marker)):
            for c, cell in enumerate(row):
                color = "rgb(0,0,0)" if cell else "rgb(255,255,255)"
                tag(
                    "rect",
                    x=self.size + (self.size * (c + 1)),
                    y=self.size + (self.size * (r + 1)),
                    width=self.size,
                    height=self.size,
                    style=f"fill:{color};stroke:none",
                )

        tag("svg", closing=True)
        file = self.get_filename(marker).with_suffix(".svg")
        file.write_text("\n".join(svg), "utf-8")
        return file


def render_text(marker: Marker):
    renderer = MarkerTXT(family=marker.family)
    return renderer.render(marker)
