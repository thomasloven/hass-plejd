# Plejd integration for Home Assistant

<img src="https://github.com/thomasloven/hass_plejd/assets/1299821/39d94f4b-bb56-43b3-9177-5be20cd91508" width="50%">

Connects to your [Plejd](https://www.plejd.com) devices using your Home Assistant Bluetooth.

This integration requires a [Bluetooth](https://www.home-assistant.io/integrations/bluetooth/) adapter which supports at least one Active connections.

Using an [EspHome Bluetooth Proxy](https://esphome.io/projects/?type=bluetooth) is recommended, but Shelly proxies will not work.
If you make your own esphome configuration, make sure the [`bluetooth_proxy`](https://esphome.io/components/bluetooth_proxy) has `active` set to `True` (default in recent versions).

## Installation

- Make sure you have a working Bluetooth integration in Home Assistant
- Make sure you have no other plejd custom components or add-ons running.
- Install the integration:
- Using HACS: [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=thomasloven&repository=hass-plejd&category=integration) or search for `Plejd`.
- Manually: Download the `plejd` directory and place in your `<config>/custom_components`.

- Restart Home Assistant
- Hopefully, your Plejd mesh will be auto discovered and you should see a message popping up in your integrations page (I recommend waiting for this rather than adding the integration manually - that way you know the Bluetooth mesh is seen by Home Assistant).
- Log in with the credentials you use in the Plejd app when prompted (email address and password)

## Supported devices

**IMPORTANT!**

In recent updates to Home Assistant something has happened to the bluetooth stack. If you experience issues like buttons spamming events into Home Assistant (like hundreds of presses per second) please update the firmware of all your Plejd devices through the Plejd mobile app.

The current latest firmware for all devices seems to be `4.xx.xx` or higher.

---

- All known Plejd lights, dimmers and relays should work.

- All buttons connected to a device or WPH-01 should work and register events when the buttons are pressed.

  - If the button is held for a while, a release even will be registered too. The required hold time doesn't seem entirely consistent, though...

- Rotary dimmer WRT-01 should register and fire events when pushed.

  - Rotations are **not** registered. This is a limitation in how Plejd works. Rotation events are not actually sent to the mesh, but directly to whatever device the WRT-01 is paired to. Therefore it is impossible to listen in on them.

- Plejd Scenes should show up and be triggerable in Home Assistant (unless hidden in the Plejd app).

  - An event entity will be triggered when they are activated (even if hidden in the Plejd app).

- Thermostat TMR-01 seems to work.

## Unsupported devices

- GWY-01 doesn't do anything.

- RTR-01 Is not actually a device but an addition to other devices.

## Cloud connection

The integration will fetch the device list and - most importantly - the cryptographic keys for the BLE communication from the Plejd cloud at launch. After that initial download, no communication is made with the cloud. All controll is local over bluetooth.

## BLE meshing

Plejd works by creating a Bluetooth BLE mesh between all the devices in your `System`.

<img width="425" height="207" alt="Image" src="https://github.com/user-attachments/assets/94725ac6-3f65-485a-b2ba-27d46fed170e" />

A controller (e.g. Home Assistant, a Plejd GQY-01 or the Plejd mobile app) can connect to the system using the cryptographic key stored in the cloud.
The controller connects to one mains powered device in the System using BLE and needs to maintain an active connection (red arrow in figure below). This device is called the Gateway by this integration.

<img width="557" height="246" alt="Image" src="https://github.com/user-attachments/assets/39f12542-a0e7-4e32-86fc-9087e98355ec" />

Each Plejd device can maintain only One connection to a controller (red arrow) at a time, and this integration can open only One connection to a System.

This means:

- If you only have one _mains powered_ Plejd device, you _can not_ controll it both from Home Assistant and the Plejd app or GWY-01 at the same time.
- If you have several Plejd devices that are so far from each other that they cannot form a BLE mesh (e.g. some in your house but one in the garage) you can not fix this just by adding a second BTproxy. You will need to first divide the devices into separate Systems in the Plejd app. Or add more Plejd devices to strengthen the mesh
- On rare occasions some devices will lose connection to the mesh if they act as Gateway. I don't know why this happens, but sometimes a factory reset of the device works. Otherwise you can disallow the device to act as Gateway from the device settings in Home Assistant.

## Debug logging

There are some loggers which may be useful for troubleshooting. They are used by adding the following to your `configuration.yaml` (pick the `pyplejd.` ones which are relevant to you):

```yaml
logger:
  default: warning
  logs:
    pyplejd.device_list: debug # Will output the list of devices pulled from the cloud - also shows the mesh index and ble address
    pyplejd.ble.connection: debug # Will show the process of connecting to the BLE mesh - this could give information if all your devices are shown but not available
    pyplejd.ble.device.123: debug # Will show the BLE traffic to and from the device with mesh index 123 - you can find the mesh index from the Plejd app or from the device_list debug output above
    pyplejd.ble.device.SCN: debug # Will show the BLE traffic related to Scenes
    pyplejd.ble.device.TME: debug # Will show the BLE traffic related to timekeeping
    pyplejd.ble.device.all: debug # Will show the BLE traffic to and from ALL devices
```

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

The Plejd name and logo is copyrighted and trademarked and belongs to Plejd AB. \
The author of this repository is not associated with Plejd AB.

> **Sidenote:**
>
> This integration makes use of a cloud API made by Plejd for use by their smartphone apps.
> The use of the API in this integration is not endorsed by Plejd, but I have been in communication with representatives of the company, and they have informally indicated an intent to look the other way as long as the API usage does not become excessive.
>
> In this time of clouds locking down and free services becoming paid, this is fantastic!
>
> Thanks, Plejd!
