# Markers #

## Marker Configuration ##

### size (int | None) ###

The size of the marker in millimeters. Used in calculating the
distance to the marker.

### invert (bool) ###

An inverted marker is turned on when the marker is *not* visible.

### family (Literal["4X4", "5X5", "6X6", "7X7"]) ###

The marker family. This indicates the number of squares that make up
the marker. In general it's recommended to just stick with `4X4`.

### filename (str) ###

Override the [filename](./rendering.md#filename-str) for a single marker.

### label (str | bool) ###

Override the [label](./rendering.md#label-str) for a single marker.

### exclude_from_ui (bool) ###

If true the marker will not be shown in the UI.

### cameras (list[str] | None) ###

A list of camera names that should detect this marker.  If this is
empty or not specified then the marker will be detected if it's
visible by any known camera.

The main advantage of setting this is that if a marker is only
associated with one camera, then an image will be published for that
marker even if the marker is not detected by the camera.

### distance_unit (Literal["mm", "cm", "m", "in", "ft"]) ###

Set the unit to use for the distance sensor. The default is `m` (meters).

### distance_decimals (int) ###

The number of decimal places to use when reporting the distance to the
marker. The default is `1`.

### attributes (Attrs) ###

A dictionary of attributes to associate with the marker. These can be
used to store additional information about the marker that will be
exposed as attributes on the marker sensors and images.

### rendering / stl_rendering / png_rendering / svg_rendering ###

See [rendering](./rendering.md).
