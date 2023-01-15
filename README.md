# home-assistant-findmy
A python script that reads local FindMy cache files to publish device locations and metadata (including those of AirTags, AirPods, Apple Watches, iPhones) to Home Assistant via MQTT.

## Disclaimer

This script is provided as-is, without any warranty. Use at your own risk.
This code is not tested and should only be used for experimental purposes.
Loading the FindMy cache files is not inteded by Apple and might cause problems.

## Description

This python script reads the FindMy cache files and publishes the location 
data to MQTT to be used in Home Assistant. It uses auto discovery so no 
further entity configuration is needed in Home Assistant. Consult the 
documentation on how to set up an MQTT broker for Home Assistant. The script
needs to be executed on macOS with a running FindMy installation. It needs
to be executed as root and in a terminal with full disk access to be able 
to read the cache files. The script must be configured using the variables
below and the mqtt client password as environment variable.

## Supports
- Devices (iPhones, iPads, MacBooks, AirPods, Apple Watches, ...)
    - including family devices
- Objects (AirTags, ...)

## How to use

1. Download this repository
2. Install dependencies: `pip3 install -r requirements.txt`
3. Change configuration in `findmy.py` to fit your setup
4. Set your MQTT client password using an environment variable `export MQTT_PASSWORD=your_password`
5. Ensure that your terminal has [full disk access](https://support.apple.com/de-de/guide/security/secddd1d86a6/web)
6. Open FindMy in the background and run `sudo python3 findmy.py`

Could I help you? [You can buy me a coffee here if you want 🙏](https://buymeacoffee.com/muehlt)
