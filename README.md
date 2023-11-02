# home-assistant-findmy
A python script that reads local FindMy cache files to publish device locations and metadata (including those of AirTags, AirPods, Apple Watches, iPhones) to Home Assistant via MQTT.

[Migration from < v1.x.x](https://github.com/muehlt/home-assistant-findmy/tree/main/.github/MIGRATION_GUIDE/1.0.2.md) • 
[Support this project](https://buymeacoffee.com/muehlt)


## Disclaimer

This script is provided as-is, without any warranty. Use at your own risk.
This code is not tested and should only be used for experimental purposes.
Loading the FindMy cache files is not intended by Apple and might cause problems.
The project is not affiliated to Apple Inc., Home Assistant or MQTT.

## Description

This python script reads the FindMy cache files and publishes the location 
data to MQTT to be used in Home Assistant. It uses auto discovery so no 
further entity configuration is needed in Home Assistant. Consult the 
documentation on how to set up an MQTT broker for Home Assistant. The script
needs to be executed on macOS with a running FindMy installation. It must 
be executed in a terminal with full disk access to be able to read the cache files.

## Supports
- Devices (iPhones, iPads, MacBooks, AirPods, Apple Watches, ...)
    - including family devices
- Objects (AirTags, ...)

## How to use

[Migration from < v1.x.x](https://github.com/muehlt/home-assistant-findmy/tree/main/.github/MIGRATION_GUIDE/1.0.2.md)

### Basic installation

1. Install using pip: `pip3 install home-assistant-findmy`
2. Setup environment variables:
    - `export MQTT_CLIENT_USERNAME=your_username`
    - `export MQTT_CLIENT_PASSWORD=your_password`
    - `export MQTT_BROKER_IP=your_broker_ip`
    - `export MQTT_BROKER_PORT=your_broker_port` (defaults to `1883`, if not set)
    - `export FINDMY_FILE_SCAN_INTERVAL=your_scan_interval` (defaults to `5` seconds, if not set)

   > You can also create a `.env` file in the directory you run the script from and add the environment variables there, e.g.:
   > ```
   > MQTT_CLIENT_USERNAME        = mqtt_client
   > MQTT_CLIENT_PASSWORD        = your_password
   > MQTT_BROKER_IP              = 192.168.178.5
   > MQTT_BROKER_PORT            = 1883
   > FINDMY_FILE_SCAN_INTERVAL   = 5
   > ```
   
   > All environment variables can also be set using [program arguments](#program-arguments), but it is highly recommended 
   > to use environment variables for your credentials.

### Configure known locations (home/work/gym/...)

Apple's "Safe Locations" are not reliable or versatile enough for your Home Assistant instance.
You can configure your own known locations in a JSON file which are then used to determine the state published to Home Assistant.
For each location you need to specify a name, latitude, longitude and a tolerance in meters (see example configuration).


*Example configuration:*
```json
{
    "home": {
        "latitude": 12.3456789,
        "longitude": 12.3456789,
        "tolerance": 70
    },
    "work": {
        "latitude": 12.3456789,
        "longitude": 12.3456789,
        "tolerance": 70
    }
}
```

If the device location is not inside the tolerance of any specified known location, 'not_home' will be shown.
If FindMy does not offer a location, the state is 'unknown'.
The first match will be returned if a device is in the range of multiple known locations.

You need to specify the path of your known locations configuration file as a program argument when running the script.

e.g. `findmy -l /path/to/known_locations.json`

## Run the script

1. Ensure that your terminal has [full disk access](https://support.apple.com/de-de/guide/security/secddd1d86a6/web)
2. Open FindMy in the background and run `findmy -l /path/to/known_locations.json`

## Program Arguments

| Argument     | Alias | Description                                                                                         |
|--------------|-------|-----------------------------------------------------------------------------------------------------|
| `--locations` | `-l`  | Path to the known locations JSON configuration file.                                                |
| `--privacy`  | `-p`  | Hides specific device data from the console output.                                                 |
| `--force-sync` | `-f`  | Disables the timestamp check and provides an update every `FINDMY_FILE_SCAN_INTERVAL` seconds.      |
| `--ip`       |       | IP of the MQTT broker.                                                                              |
| `--port`     |       | Port of the MQTT broker.                                                                            |
| `--username` |       | MQTT client username.                                                                               |
| `--password` [**Warning**] |       | MQTT client password. **Only for rare test cases!** Avoid setting the password using this parameter. |

> **Warning**: For security reasons, it's advised not to set the password using the `--password` parameter, except in rare test cases. Always prefer setting it via the environment variable.

## Versions

### 1.1.0
In very rare occasions, or if you have changed the code before, this version might
lead to changed device IDs being propagated to your Home Assistant instance.
- Fix invalid device IDs by removing special characters
- Cleanup of device IDs client side for consistency
- Minor improvements

### 1.0.X - Breaking changes
- Configuration is now done solely via environment variables and a JSON file for known locations
- Installation using pip is now possible
- Device data is only updated if the location timestamp changed in FindMy (skip with `-f` flag)
- Improved terminal output
- Minor improvements

### 0.0.2
- Adjusted device names to fit [recent MQTT changes](https://community.home-assistant.io/t/psa-mqtt-name-changes-in-2023-8/598099) ([PR](https://github.com/muehlt/home-assistant-findmy/pull/4))

### 0.0.1
- Initial version

## License

See [LICENSE.md](https://github.com/muehlt/home-assistant-findmy/blob/main/LICENSE.md)

## Roadmap

- Support DeviceGroups
- Write comprehensive tests

Could I help you? [You can buy me a coffee here if you want 🙏](https://buymeacoffee.com/muehlt)
