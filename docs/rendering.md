# Rendering #

This configuration controls how markers are rendered, which means
controlling things like their size when you generate SVG, PNG, or STL
files for creating physical markers.

## Common Rendering Configuration (rendering) ##

These configuration options are common to all rendering types. You can
specify defaults for all types of rendering, or you can specify it just
for a specific type.

```yaml
marker_defaults:
  rendering:
    filename: 'marker-$tag_id'
    size: 50
  stl_rendering:
    size: 25
```

### filename (str) ###

The format of the filename to use when creating markers. This is used
as a template and you can use variables from the marker configuration
to customize the filename. The default is `marker-$tag_id`. A file
extension (such as `.png`, `.stl`, or `.svg`) will be appended when
creating markers.

### label (str | bool) ###

The template for the label to use when rendering the marker. Like with
`filename` you can use configuration variables in the template. If you
don't want to include a label when creating markers you can set this
to `false`. You can also use `true` to use the default label template
(which is `$tag_id : $name`).

### size (float) ###

The size of the marker grid (in millimeters). Note that this is not
the overall size of the marker, but the size of each square in the
grid.

So, for example, if you set this to 25 then render an STL marker, the
actual marker will be 150 mm x 150 mm for a 4X4 marker. (25 * 6 = 150,
6 because the marker is 4x4 and has a 1 square margin around the
outside).

### directory (Path) ###

The output directory to save the marker files in. The default is the
current working directory.

## STL Rendering Configuration (stl_rendering) ##

These settings are used when rendering markers to STL files for 3D
printing.

### grid_thickness (float) ###

The thickness of the main portion of the marker (the part that
contains the black and white grid). This is in millimeters and the
default is `5`.

### base_thickness (float) ###

The thickness of the base of the marker. This will be a solid white
layer underneath the main portion of the marker. You don't necessarily
need this and can set it to 0 if you will be printing the markers with
a multi-extruder printer. If you print with a single extruder printer
then having a base provides you the ability to print the white portion
of the marker and then print the black parts and glue them into the
empty spaces. The default is `1` (mm).

### hole_diameter (float) ###

If this is greater than 0 then mounting holes will be included at the
corners of the marker with this diameter (in millimeters). The default
is `0` (to not include holes).

### hole_depth (float) ###

If this is greater than 0 then the mounting holes will only extend
this deep into the back side of the marker. This can be used to create
holes for heat-set inserts, or just to create a hole that you can put
a coarse-thread screw into that won't be visible from the front of the
marker.

### hole_offset (float) ###

How far from the edge of the marker to center the mounting holes.
The default is `10`.

### spacer_height (float) ###

If this is greater than 0 then a "spacer" will be added to the back of
the marker. This can be helpful when mounting the marker to a surface
that isn't really flat. The default is `0` (no spacers).

### spacer_diameter (float) ###

The diameter of the spacers. The default is `20`.

### label_size (float) ###

The size of the label (as a percentage of the total marker size).

The default is `0.75`, which will scale the label to be roughly 75% of
the width of the marker.

### label_font (str) ###

The font to use for the label. This can be any font that OpenSCAD
understands. The default is `Helvetica:style=Bold`.

### label_depth (float) ###

How deep to engrave the label into the back of the marker. If this is
negative then the label will be embossed instead of engraved.

### drill_guide (bool) ###

If true then an additional STL file will be created with a printable
drilling guide to help you drill holes in exactly the right place for
mounting your marker. Default is `true`.

### scad_only (bool) ###

If true then only the OpenSCAD file will be created and no STL files
will be rendered. This is mostly useful while debugging the STL
generating code, as you can run OpenSCAD and have it show you what the
resulting object would look like while skipping the time-consuming
process of actually generating STLs. The default is `false`.

### keep_scad (bool) ###

If true then the `*.scad` files will be kept after rendering the STL.
The default is `false` which means the `.scad` files are deleted after
the `.stl` files have been generated.

## PNG Rendering Configuration (png_rendering) ##

### dpi (int) ###

The dots-per-inch to render the PNGs at. The default is `72`.

## SVG Rendering Configuration (svg_rendering) ##

Rendering to SVG has no additional configuration options beyond the
common ones.
