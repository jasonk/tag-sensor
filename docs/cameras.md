# Cameras #

In order to detect tags, the system needs to know how to find cameras.
For the simplest case (using the Home Assistant add-on) all you need
to specify is the id of each camera that you want to use.

```yaml
cameras:
  - id: bins_fluent
  - id: garage_fluent
```

This is from an early version of my own configuration. Initially I had
just a "bins", which have is an old camera that I mounted at the
corner of the garage pointing straight down at the area where our
trash and recycling bins are stored.

The garage camera is used to detect whether the garage door is open or
closed, by looking for a tag on the inside of the garage door.

## Camera Configuration ##

### id (str) ###

The unique identifier for the camera. This is primarily an internal
ID, but the interface may use it to identify the camera. When using
the Home Assistant interface if the camera doesn't have `entity_id`
configured, then the interface will assume that the `entity_id` is
`camera.<id>`.


### http (HttpOptions | None) ###
### overlay (OverlayOptions) ###
### ignore_detections (bool) ###
### save_images (bool) ###
### data_dir (Path | None) ###
### address (str | None) ###
### username (str | None) ###
### password (str | None) ###
### channel (str | int | None) ###
### stream (str | None) ###
### entity_id (str | None) ###
### attributes (Attrs | None) ###
### exclude_from_ui (bool) ###

### calibration (CalibrationConfig) ###
### interface (InterfaceConfig | str | None) ###
