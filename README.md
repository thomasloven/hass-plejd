Plejd integration for Home Assistant
===

This integration is a work in progress.

I do not guarantee it will work or even that it will not harm your system. I don't see what harm it *could* cause, but I promise nothing.

## Installation for testing

- Make sure you have a working Bluetooth integration in Home Assistant (a bluetooth proxy should work too)
- Put the `plejd` directory in your `<config>/custom_components`.
- Restart Home Assistant
- Hopefully, your Plejd mesh will be auto discovered and you should see a message popping up in your integrations page.
- Log in with the credentials you use in the Plejd app when prompted (email address and password)

## Current limitations

- I only have a single DIM-01 device, so that's the only one I know for sure works.
- Only one channel per device is expected to work right now. E.g. only one lamp connected to a DIM-02 will show up in Home Assistant.

## About connections

Plejd devices doesn't seem to like to have multiple connections going.
Once a controller like the official Plejd app or Home Assistant connects, they will hide their precense from everyone else until a time after that connection is broken.

That means that if you only have one Plejd device you may not be able to use Home Assistant and the app to controll the device at the same time, and either may have a hard time connecting while the other is running.

Even after turning off the app or Home Assistant it may take 30 minutes to several hours before the othe rcan connect again. Turning off bluetooth on the last connected device or cutting power to the Plejd for a minute may help.


## Getting more debug information

Add this to your Home Assistant configuration.yaml to get as much information as possible

```yaml
logger:
  default: warn
  logs:
    custom_components.plejd: debug
```
