# Plejd integration for Home Assistant

Connects to your [Plejd](https://www.plejd.com) devices using your Home Assistant Bluetooth.

This integration requires a [Bluetooth](https://www.home-assistant.io/integrations/bluetooth/) adapter which supports at least one Active connections.

Using an [EspHome Bluetooth Proxy](https://esphome.io/projects/?type=bluetooth) is recommended, but Shelly proxies will not work.
If you make your own esphome configuration, make sure the [`bluetooth_proxy`](https://esphome.io/components/bluetooth_proxy) has `active` set to `True`.

## Installation for testing

- Make sure you have a working Bluetooth integration in Home Assistant (a bluetooth proxy should work too)
- Make sure you have no other plejd custom components or add-ons running.
- Install the integration:

  - Either: Download the `plejd` directory and place in your `<config>/custom_components`.
  - Or: Add this repo (`thomasloven/hass_plejd`) as a custom repository in HACS, add the integration from HACS

- Restart Home Assistant
- Hopefully, your Plejd mesh will be auto discovered and you should see a message popping up in your integrations page.
- Log in with the credentials you use in the Plejd app when prompted (email address and password)

> Note: I will not have this added to the HACS default repository. My hope is to have it added to Home Assistant instead.

## Supported devices

- All known Plejd dimmers and relays should work (except DAL-01).

- All known Plejd lights except OUT-01 should work, but white balance is not supported.

- Pushbutton WPH-01 should work.

  - An event entity will be triggered when each button is pushed

- Rotary dimmer WRT-01 should register and fire events when pushed (untested).

  - Rotations are **not** registered. This is a limitation in how Plejd works. Rotation events are not actually sent to the mesh, but directly to whatever device the WRT-01 is paired to. Therefore it is impossible to listen in on them.

- Plejd Scenes should show up and be triggerable in Home Assistant (unless hidden in the Plejd app).
  - An event entity will be triggered when they are activated (even if hidden in the Plejd app).

## Unsupported devices

- GWY-01 doesn't do anything.

- EXT-01 doesn't do anything

- RTR-01 Is not actually a device but an addition to other devices.

- DAL-01 is not supported, because I don't have access to one.

- OUT-01 is not supported, because it is unreleased, and I don't have access to one.

**If you have a DAL-01, OUT-01 or WRT-01 device, please get in touch to help me get them supported.**

## Other integrations

There area several other integrations for Plejd with Home Assistant available, made by some awesome people.

The following is a list of the ones I have looked at in order to create this one, and how this one is different.

I could not have made this one without their great job in decoding the Plejd cloud API and Bluetooth communication protocol.

|                                                                    |                                                                                                                                                                     |                                                                                                                                                                                                                                                           |
| ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [hassio-plejd](https://github.com/icanos/hassio-plejd)             | [@icanos](https://github.com/icanos)                                                                                                                                | Works only with Home Assistant OS.<br> Relies on MQTT for communication.<br> Requires exclusive access to a Bluetooth dongle.<br> Does not support Bluetooth Proxy.                                                                                       |
| [plejd2mqtt](https://github.com/thomasloven/plejd2mqtt)            | [@thomasloven](https://github.com/thomasloven)                                                                                                                      | Somewhat outdated stand-alone version of the above.<br> Relies on MQTT for communication.<br> Requires exclusive access to a Bluetooth dongle.<br> Does not support Bluetooth Proxy.<br> Does not support switches or scenes.                             |
| [ha-plejd](https://github.com/klali/ha-plejd)                      | [@klali](https://github.com/klali) <br> (also check [this fork](https://github.com/bnordli/ha-plejd/tree/to-integration) by [@bnordli](https://github.com/bnordli)) | Does not communicate with the Plejd API and therefore requires you to extract the cryptokey and device data from the Plejd app somehow.<br> No auto discovery.<br> Requires exclusive access to a Bluetooth dongle.<br> Does not support Bluetooth Proxy. |
| [homey-plejd](https://github.com/emilohman/homey-plejd)            | [@emilohman](https://github.com/emilohman)                                                                                                                          | For Homey                                                                                                                                                                                                                                                 |
| [homebridge-plejd](https://github.com/blommegard/homebridge-plejd) | [@blommegard](https://github.com/blommegard)                                                                                                                        | For Homebridge                                                                                                                                                                                                                                            |
