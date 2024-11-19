# Making Markers #

Once you have configured your markers as described in
[Configuration](configuration.md), you can use the `tag-sensor` tool
to render them:

* `tag-sensor make-markers`

By default it will go through every marker in your configuration file and
render `.stl` and `.svg` files for each one into the current directory.
Run `tag-sensor make-markers --help` to see what options you have to
change what it does.

## Making STL Markers ##

The `.stl` rendering is the most complex and has the most features,
because it's the one I use the most. When you render the STL markers,
it actually produces three files as output instead of one. It will
render a `<filename>.scad` file which is an [OpenSCAD][openscad]
source file that contains the whole marker, and then it will also render
`<filename>.black.stl` and `<filename>.white.stl` files for the black
and white parts of the marker.

[openscad]: https://www.openscad.org/

### Printing with a multi-extruder printer ###

With a multi-extruder printer you can load up the whole thing and
print it in one shot. The way I do this on my Prusa XL is to open both
the `.stl` files in PrusaSlicer at once. PrusaSlicer will ask you if
it should be treated as two parts of the same file and you should
answer `yes`. Then you can set extruder 1 to print the black part and
extruder 2 to print the white part, load the proper filaments, and
away you go.

When printing with a multi-extruder printer you should print it face
down, so that you get a nice smooth finished surface on the part that
people will see.

### Printing with a single-extruder printer ###

If your printer can only print one color at a time you can still print
markers, you just have to do it in two steps. When rendering for this
method I suggest you include these settings:

```yaml
stl_rendering:
  # You can't include spacers because you need to print it with the
  # grid facing up.
  spacer_height: 0
  # You could keep the label if your printer is really well tuned, but
  # it often just causes problems when starting out with the label on
  # the bed, so I recommend turning it off.
  label_depth: 0
  # Make sure you *do* set a non-zero value for base_thickness, so you
  # get "pockets" you can insert the black pieces into.
  base_thickness: 3
```

After you have your `.stl` files, print the white one on it's back
with the grid facing up so you end up with a marker that just has the
black squares missing. Then you can print the black part separately
and glue them into the pockets on the white part.
