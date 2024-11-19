# Tag Sensor #

_Allows you to define sensors that track whether a physical marker is
visible to a camera._

What can you use this for?  [ArUco markers][aruco] are commonly used
for grand things like robot positioning, but I created this toolkit
for a far more mundane reason: I wanted [Home Assistant][hass] to be
able to detect whether my trash and recycling bins had been taken to
the curb, and send me an alert if there is a pickup the next morning
and the bin is still sitting next to the house.

Some other things it can be useful for:

* Have a camera in your garage? Paint a marker on the garage door to
  tell if it's open or closed. Paint a marker on the floor, if it's
  not detected then there is likely a car in the garage covering it
  up.
* Add markers to all your storage bins, and put a camera in your
  storage room. Easily determine which bins are in storage and which
  are somewhere else.
* ~The ultimate presence detection! Put cameras on the ceiling in every
  room, and tattoo a marker on top of your bald head!~ Hmm, maybe not
  that one.

![Example Tags](./images/bins.png)

[aruco]: https://www.uco.es/investiga/grupos/ava/portfolio/aruco/

## What is an ArUco marker? ##

An ArUco marker is a grid of black and white squares that is similar
to a QR Code. But where a QR code can encode a string of arbitrary
text, the only information in an AruCo marker is a single number.

These markers are designed to be easy to detect in an image, and with
the right preparation they can provide enough information to allow you
to determine their "pose" (the distance, orientation, and angle of the
marker in relation to the camera that detected it).

AruCo markers come in a variety of families, but we only support
a few.  The supported families are: `4X4`, `5X5`, `6X6`, and `7X7`.
The family determines the dimensions of the grid that encodes the
number for the marker. The `4X4` family is a grid of 4 rows and
4 columns, and you can probably guess what that means about the other
families.

Unless you have a compelling reason to switch I recommend sticking
with `4X4` because the small number of squares in the grid makes it
easy to detect from a distance, and it's simple enough that for many
purposes you can even tape out the grid and paint the squares by hand.

FYI: "AruCo" stands for "Augmented Reality University of Cordoba".

## Installation ##

[![Open this add-on in your Home Assistant instance.][addon-badge]][addon]

```shell
pip install tag-sensor
```

## Getting Started (Configuration) ##

Take a look at:

* [Configuration Options](./CONFIGURATION.md)
* [Making Markers](./MARKERS.md)
* [Contributing](./CONTRIBUTING.md)

## Help ##

Problems?

- [Home Assistant Community Forum][forum].
- [/r/homeassistant subreddit][reddit].
- [Open an issue on GitHub][issues].

## Author ##

Created by [Jason Kohles][jasonk].

For a full list of all authors and contributors, check [the
contributor's page][contributors].

[contributors]: https://github.com/jasonk/tag-sensor/graphs/contributors
[issues]: https://github.com/jasonk/tag-sensor/issues
[forum]: https://community.home-assistant.io/
[reddit]: https://reddit.com/r/homeassistant
[repository]: https://github.com/jasonk/tag-sensor
[jasonk]: https://github.com/jasonk
[addon-badge]: https://my.home-assistant.io/badges/supervisor_addon.svg
[addon]: https://my.home-assistant.io/redirect/supervisor_addon/?addon=ed6f055f_tag_sensor&repository_url=https%3A%2F%2Fgithub.com%2Fjasonk%2Ftag-sensor
