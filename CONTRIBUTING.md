## Installation ##

To get started, you'll need [Python][python] (3.11 or later),
and [poetry][poetry]. Clone the repo, then run `poetry install`.

### Frame providers ###

In order to detect markers, the library needs to be able to get frames
from any of the cameras that you want to use to detect them. With the
Home Assistant integration we just use the camera API to get frames
from any camera that Home Assistant can access. For other uses you
need to provide configuration for a `frame_provider` that can get
a frame from whatever camera you are using.

I've included three frame providers, and they are simple enough that
you could write a custom one if needed.

#### Home Assistant Frame Provider ####

This is the one that is used by the Home Assistant integration. You
normally wouldn't need to configure this one yourself, as the
integration will handle it for you, but configuring it can be useful
for testing and development, if you want to just run the tool from the
command line without having to setup the integration.

```yaml
frame_provider:
  provider: homeassistant
  server: http://homeassistant.local:8123
  token: YOUR_ACCESS_TOKEN
  timeout: 10
```

The `server`, `token`, and timeout options are all optional, if you
don't specify them in the config file then `server` will look in the
environment for `$HASS_SERVER` qnd use that, or default to
`http://homeassistant.local:8123`, Similarly `token` will look for
`$HASS_TOKEN` in the environment, and `timeout` will default to 10
(it's in seconds).

#### Reolink Frame Provider ####

I wrote this mostly for testing purposes, since I have Reolink
cameras.  When using this some of the configuration goes on the camera
rather than the provider.

```yaml
cameras:
  - id: my_first_camera
    use_https: true
    hostname: 192.168.1.150
    username: admin
    password: 'another-admin-password'

frame_provider:
  provider: reolink
  username: admin
  password: YOUR_PASSWORD
  use_https: false
  timeout: 10
```

If `use_https`, `username`, or `password` are specified for the
specific camera then it will use those values, if they aren't then it
will use the value from the `frame_provider` as a default. If
`hostname` isn't provided then it will assume that the camera's `id`
is also it's hostname and try to connect to it that way (which is
likely to not work).

#### Dummy Frame Provider ####

The dummy frame provider is just for testing and development. It gets
frames by just looking in a directory for an image with the name of
the camera.

```yaml
cameras:
  - id: my_camera

frame_provider:
  provider: dummy
  directory: ./images
```

With this configuration, when it attempts to detect markers using the
camera `my_camera`, it will just load whatever image is found in
`images/my_camera.jpg` and use that.

## Debugging STL Rendering ##

When working on the STL rendering code it can be helpful to set
`scad_only: true` as an option in `stl_rendering`, or run `tag-sensor
make-stl-markers --scad-only <marker_id..>`.

That way, when you run `tag-sensor make-stl-markers` it only generates
the OpenSCAD file and skips the time-consuming STL file generation.

Then you can have OpenSCAD open rendering that file and every time you
run it you'll see the updated version rendered in OpenSCAD.
