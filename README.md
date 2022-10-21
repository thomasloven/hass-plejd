Plejd integration for Home Assistant
===

No Plejd hub needed.

This integration is a work in progress.

I do not guarantee it will work or even that it will not harm your system. I don't see what harm it *could* cause, but I promise nothing.

## Installation for testing

- Make sure you have a working Bluetooth integration in Home Assistant (a bluetooth proxy should work too)
- Make sure you have no other plejd custom components or add-ons running.
- Put the `plejd` directory in your `<config>/custom_components`.
- Restart Home Assistant
- Hopefully, your Plejd mesh will be auto discovered and you should see a message popping up in your integrations page.
- Log in with the credentials you use in the Plejd app when prompted (email address and password)


## Getting more debug information

Add this to your Home Assistant configuration.yaml to get as much information as possible

```yaml
logger:
  default: warn
  logs:
    custom_components.plejd: debug
```

## Other integrations

Here are some other Plejd integrations by some awesome people and how this is different:

I've pulled inspiration from all of them.

| | | |
|---|---|---|
|[hassio-plejd](https://github.com/icanos/hassio-plejd) | [@icanos](https://github.com/icanos) | Works only with Home Assistant OS.<br> Requires exclusive access to the Bluetooth dongle.<br> Does not support Bluetooth Proxy. |
|[plejd2mqtt](https://github.com/thomasloven/plejd2mqtt) | [@thomasloven](https://github.com/thomasloven) | Relies on MQTT for communication.<br> Requires exclusive access to the Bluetooth dongle.<br> Does not support Bluetooth Proxy.<br> Does not support switches or scenes. |
|[ha-plejd](https://github.com/klali/ha-plejd) | [@klali](https://github.com/klali) | Does not communicate with the Plejd API and therefore requires you to extract the cryptokey and device data from the Plejd app somehow.<br> No auto discovery.<br> Requires exclusive access to the Bluetooth dongle.<br> Does not support Bluetooth Proxy.  |
| [homey-plejd](https://github.com/emilohman/homey-plejd) | [@emilohman](https://github.com/emilohman) | For Homey |
| [homebridge-plejd](https://github.com/blommegard/homebridge-plejd) | [@blommegard](https://github.com/blommegard) | For Homebridge |
