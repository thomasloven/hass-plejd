Plejd integration for Home Assistant
===

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
