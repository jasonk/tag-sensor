# Configuration #

The main thing you need to configure in this file is the `markers`
section, which contains information about the markers you want to
track. This configuration can also provide all the information needed
to create the physical markers themselves. There are several options
for creating markers. My favorite is 3D printing them, but the tool
can also produce `.png` or `.svg` files that you can print out and
laminate, and if you stick with the recommended `4X4` family the
markers are even simple enough that you could easily paint them by
hand.

Lets look at what is in the `example-config.yaml` file in this repository,
which should give you a good idea of what you can configure.

This example is basically the configuration that I use for the markers
around my house. To start out with I configure some cameras, because
I don't want it to try and find markers in all of my cameras, since
it's unlikely that the trash bin would be detected in the kitchen, for
example.

```
cameras:
  - id: bins_fluent
  - id: driveway_fluent
  - id: garage_fluent
```

The "bins" camera I have is an old camera that I mounted at the corner
of the garage pointing straight down at the are where the bins are
normally stored, so it is the one that almost always detects them.
I included the driveway camera because if it detects a tag it usually
means that the wind blew one of the empty bins over. The garage camera
reports if the garage door is open by detecting a marker painted on
the inside of the door.


The next section is the markers themselves.

```
markers:
  - id: 'recycling_bin_parked'
    tag_id: 21
    name: 'Recycling Bin Parked'
  - id: 'trash_bin_parked'
    tag_id: 22
    name: 'Trash Bin Parked'
  - id: 'compost_bin_parked'
    tag_id: 23
    name: 'Compost Bin Parked'
  - id: 'garage_door_open'
    name: 'Garage Door is Open'
    tag_id: 30
    invert: true
```

As you can see, I have defined markers for three different bins, and
one for the garage door detection.

Then we have marker defaults. These are default values that will be
added to all markers that don't have configured values for these
fields.

```
marker_defaults:
  family: '4X4'
  stl_rendering:
    grid_thickness: 4.0
    base_thickness: 4.0
    hole_diameter: 5.8
    hole_depth: 5
    spacer_height: 5
    spacer_diameter: 20
    label_depth: 1
    label_size: 75
```

### Marker Configuration Options ###

#### id ####

The `id` field is a unique identifer for the marker. When using the
Home Assistant integration this will also be part of the `entity_id`
for the entities created by the integration. Each marker will provide
a `binary_sensor.<id>` entity that will be `on` when the marker is
detected, and also an `image.<id>` entity that will show you the
captured image where the marker was detected, with the marker's position
marked on it.

#### tag_id ####

The `tag_id` is the number that will be encoded in the AruCo tag.
Regardless of which family you are using, the tag will always be
a number in the range `0-999`.

IMPORTANT NOTE: Not all `tag_id` numbers are equal. The AruCo library
families include both the size of the grid, and the number of markers
that can be represented. If you only need a few markers then you
should pick `tag_id` values between `0` and `49`. The detection code
includes error correction to help avoid mis-identifying markers. The
details of how this works are complicated and not really relevant for
this application, the only thing you really need to know is that if
you need fewer than 50 total markers then you should only use values
between `0` and `49`. These values will produce markers that are more
distinct from one another and easier to differentiate.

The good news is you don't really have to decide how many markers
you'll need. If you start with values under `50` and find that you ran
out, then you can just start using larger values. The library will
adjust automatically. If you are using the default `4X4` family then
while stick with small values the detection will use `DICT_4X4_50` as
the detection dictionary. If you find you need more values, then you
can just use larger numbers. Once you've defined a marker with a value
of `50` or greater, then the detection will switch to the
`DICT_4X4_100` dictionary. If you really go crazy with markers then you
might end up switching to the `DICT_4X4_250` dictionary, or even the
`DICT_4X4_1000` dictionary.

#### size ####

The `size` field is the size of the marker (in millimeters). This
serves two purposes, first it used when creating `.stl`, `.png`, or
`.svg` files for producing physical markers, and secondly if you have
calibrated your cameras then it can be used in calculating the
distance between the marker and the camera.

(TODO: Although this claims the size is in millimeters, I'm really
only sure about that for `.stl` rendering, for images I need to confirm)

#### family ####

The `family` determines the size of the grid as discussed above under
"What is an ArUco marker?" Generally you want to either leave this
unset (it defaults to `4X4`) or set it in the `marker_defaults`
section so all your markers use the same family.

It is possible to set it on a per-marker basis, but the library will
end up doing more work to detect the markers if you use more than one
family, because for every frame it will have to run a detector for
each family that might possibly appear in that frame.

#### invert ####

The `invert` setting simply inverts the logic of the sensor. If
`invert` is true then the sensor value will be `on` if the marker was
*not* detected by any camera.

#### stl_rendering / png_rendering / svg_rendering ####

Each of these sections provide configuration used when rendering that
kind of physical marker. Recording the values used in your
configuration and then rendering from that configuration is the best
way to handle this, especially if you are making markers that will
live outside where you might need to replace them in a few years and
probably won't remember exactly what settings you used the first time.

More detail on these settings is in the "Making Markers" section below.

## Rendering Options ##

The toolkit can produce `.stl`, `.png`, and `.svg` files for creating
the actual markers that will be detected.

For all of these formats there are a few common options available:

### size ###

The size of the marker grid in millimeters. Note that the default is
`25`, which might strike you as small, but this size is the size of
each individual square in the grid, not the overall size of the whole
marker.

To determine the overall size of the whole marker take the number from
the family you are using (`4X4 = 4`, `5X5 = 5`, etc) then add 4 (for
the border and the quiet zone) and multiply that by size. So, for example,
with the default size of `25`, a `4X4` marker would be `200` millimeters
per side (`(4+4)*25 == 200`).

### filename ###

A template for the base name of the file that will be created. (See
"String Templates" section below for more information on templates).

The default value is `marker-$tag_id`.

### label ###

A template for the label that will be placed on the marker. This works
just like filename, except you can also use `False` to not render
a label, or `True` to use the default label template. The default
template is `$tag_id : $name`.

(TODO: I don't think .png or .svg renderers currently do anything with
the label)

#### String Templates ####

The `filename` and `label` options are both templates, which means you can
provide variables that start with `$` and will substitute in values from
the marker itself.

## STL Settings ##

### grid_thickness / base_thickness ###

These set the thickness of the main part of the marker. The black and
white part of the marker will be as thick as `grid_thickness`
specifies, and if you set `base_thickness` to a non-zero value then
the marker will have an all-white base layer of this thickness
underneath the grid.

This base layer is crucial if you are printing the marker in two parts
and gluing them together, and optional otherwise (though if you render
a label without having a base then you may run into problems.

### hole_diameter / hole_depth / hole_offset ###

If you want mounting holes included then you can set these values to
determine where and how big they will be.

The `hole_diameter` is the diameter of the hole, and `hole_depth` is
how deep to make the holes. If you want the holes to go all the way
through you can use any value larger than the total thickness of the
marker (`grid_thickness + base_thickness + spacer_height`). If you
look at the `example-config.yaml` file you'll see that I use these
settings:

```yaml
grid_thickness: 4.0
base_thickness: 4.0
spacer_height: 5
hole_diameter: 5.8
hole_depth: 5
```

This gives me a marker that is 8mm thick, with 5mm spacers at the
corners, and a hole that doesn't go all the way through, but is the
perfect size to add in M4x6 threaded heat-set inserts.

The `hole_offset` defaults to 10, meaning that there will be holes at
each corner, with their centers 10 millimeters from both edges of the
marker (which puts them in the outer white "quiet area" of the marker).

### spacer_height / spacer_diameter ###

If `spacer_height` is non-zero then the marker will have spacers added
at each corner. I added this feature because the lids on my trash and
recycling bins are not flat, so this gives them little "legs" at the
corner to make mounting them easier without deforming the lid.

The spacers are cylinders with a diameter of `spacer_diameter` and are
centered at the same point as the holes.

### label_size / label_depth / label_font ###

If `label_depth` is non-zero then a label will be added to the back of
the marker. By default the label is "engraved" into the back, but if
you set `label_depth` to a negative value then it will be "embossed"
instead.

The label is always centered on the back of the marker, and you can
roughly control the size by using `label_size`. This is specified as
a percentage of the overall size, because trying to size text in
OpenSCAD gets weird and complicated. The default value is `75`, which
means that the text gets rendered, then resized to 75% of the markers
total size, which generally works out to be a reasonable size.

You can also change the `label_font` if you want to use a different
font.

I included the label option mostly to make it easier to keep track of
which label is which when you are printing several of them and then
attaching them to things. Since the label isn't visible once it's
mounted anyway I haven't put much effort into making it easy to get
exactly the font/size/position you want (you might also notice that
it's technically upside-down).
