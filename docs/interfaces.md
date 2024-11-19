# Interfaces #

An `interface` tells the tool how it can communicate with the cameras.
There are several existing interface providers for different kinds of
cameras.

There are two places in the configuration where you can configure an
interface. First there is top-level `interfaces` option where you can
configure one or more interfaces for groups of similar cameras:

```
interfaces:
  fake:
    provider: dummy
    directory: './tests/images'
```

Secondly you can configure an interface for a specific camera. If all
of your cameras can use the same interface, then you can just set that
as a default value:


```
interfaces:
  http:
    provider: http
    verify_ssl: false
    follow_redirects: false
    timeout: 15
camera_defaults:
  interface: http
```

If you have more than one kind of camera, you can have multiple
interfaces. It's also possible to have a separate interface for each
individual camera.

```
cameras:
  - id: camera1
    interface:
      provider: http
      address: 192.168.1.100
      username: admin
      password: ''
      use_ssl: false
  - id: camera2
    interface:
      provider: http
      address: 192.168.1.101
      username: admin
      password: ''
      use_ssl: false
  - id: camera3
    interface:
      provider: http
      address: 192.168.1.101
      username: admin
      password: ''
      use_ssl: false
```

If you find yourself doing this though, you may want to consider
letting them share. There are a handful of options that are commonly
different per-camera that can be specified on the camera instead of
the interface (`address`, `username`, `password`, `channel`, and
`stream`).

So instead of all that duplication, you could do it like this instead:

```
interfaces:
  main:
    provider: http
    username: admin
    password: ''
    use_ssl: false
camera_defaults:
  interface: main
cameras:
  - id: camera1
    address: 192.168.1.100
  - id: camera2
    address: 192.168.1.101
  - id: camera3
    address: 192.168.1.102
```

## Dummy Interface Provider ##

The `dummy` interface provider is mostly used for development,
although you could also use it test the tool without a camera.

When asked to get an image from a camera, instead of connecting to an
actual camera what the dummy provider does is to look in a configured
directory for either a file named `<camera_id>.png`, or a directory
named `camera_id`. If a file is found then every time the dummy
provider is asked to get an image for that camera, it just returns the
contents of that file every time.

If a directory is found instead of a file, then it finds all files in
that directory with a `.png` extension, and when asked for an image
from that camera, it picks one of those files at random and returns
it, removing it from the list. If it's asked for an image and the list
is empty then it will scan the directory again to reload the list of
image.

```
provider: dummy
directory: './dummy-images'
```

## HTTP Interface Provider ##

The http provider can be used for cameras that have a basic interface
that returns an image.

```
provider: http
# Generate a suitable URL based on camera configuration properties
url_template: 'https://${ address }/snapshot.jpg'
# Add custom headers
headers:
  Authorization: Bearer ---token---
# Add url parameters
params:
  channel: 1
verify_ssl: true
follow_redirects: true
timeout: 5
```

## Home Assistant Provider ##

The Home Assistant provider can connect to a Home Assistant instance
and get an image from any camera that Home Assistant has access to.

This example also shows how you can use environment variables to avoid
putting passwords into your configuration file. Although in this case
the environment variables listed are used by default, so you could
just use `provider: homeassistant` without any other options and it
would work the same.

```
provider: homeassistant
server: '{{ env.HASS_SERVER }}'
token: '{{ env.HASS_TOKEN }}'
```

## Reolink Camera Provider ##

The Reolink camera provider is a thin wrapper around the HTTP provider
that knows how to assemble a URL for Reolink cameras and also how to
interpret the response if it gets an error.

The normal HTTP provider doesn't handle the error responses well,
because Reolink cameras return *weird* error responses (you ask them
for an image at a URL that normally returns an image, and the respond
with a `200 OK` status, but instead of an image they give you back
JSON while claiming it's HTML).

```
provider: reolink
username: 'admin'
password: ''
use_ssl: true
verify_ssl: false
```

## Reolink NVR Provider ##

If you have a Reolink NVR then getting images from it rather than from
the camera directly. With this setup, you specify connection
information for the NVR when setting up the interface, then all you
have to specify for each camera is the channel (if you don't specify
a channel, it will assume the camera id is the name it has in the NVR
and find the channel from that).

```
provider: 'reolink-nvr'
address: '192.168.0.200'
username: '{{ env.REOLINK_USERNAME }}'
password: '{{ env.REOLINK_PASSWORD }}'
use_ssl: true
verify_ssl: false
```

When specifying the camera channel you can use either the channel
number, or the name that the NVR knows the camera by, and the provider
will use the NVR API to find the other information it needs to access
the camera.

On the camera you can also specify the `stream` to use.
