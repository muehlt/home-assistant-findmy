#!/usr/bin/python3

# .                                       .           .                   .          
# |                                 o     |           |        ,- o       |          
# |-. ,-. ;-.-. ,-. --- ,-: ,-. ,-. . ,-. |-  ,-: ;-. |-  ---  |  . ;-. ,-| ;-.-. . .
# | | | | | | | |-'     | | `-. `-. | `-. |   | | | | |        |- | | | | | | | | | |
# ' ' `-' ' ' ' `-'     `-` `-' `-' ' `-' `-' `-` ' ' `-'      |  ' ' ' `-' ' ' ' `-|
#                                                             -'                  `-'
# made with ♡ by muehlt
# github.com/muehlt
# version 1.0.0
#
# DESCRIPTION:  This python script reads the FindMy cache files and publishes the location
#               data to MQTT to be used in Home Assistant. It uses auto discovery so no
#               further entity configuration is needed in Home Assistant. Consult the
#               documentation on how to set up an MQTT broker for Home Assistant. The script
#               needs to be executed on macOS with a running FindMy installation. It needs
#               to be executed as root and in a terminal with full disk access to be able
#               to read the cache files. The script must be configured using the variables
#               below and the mqtt client password as environment variable.
#
# DISCLAIMER:   This script is provided as-is, without any warranty. Use at your own risk.
#               This code is not tested and should only be used for experimental purposes.
#               Loading the FindMy cache files is not inteded by Apple and might cause problems.
#
# LICENSE:      See the LICENSE.md file of the original authors' repository
#               (https://github.com/muehlt/home-assistant-findmy).

from datetime import datetime
import math
import re
import time

import click
import paho.mqtt.client as mqtt
import os
import json
from unidecode import unidecode
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

load_dotenv()

###################
#  CONFIGURATION  #
###################

MQTT_BROKER_IP = os.environ.get('MQTT_BROKER_IP')
MQTT_BROKER_PORT = int(os.environ.get('MQTT_BROKER_PORT')) or 1883
MQTT_CLIENT_USERNAME = os.environ.get('MQTT_CLIENT_USERNAME')
MQTT_CLIENT_PASSWORD = os.environ.get('MQTT_CLIENT_PASSWORD')
FINDMY_FILE_SCAN_INTERVAL = int(os.environ.get('FINDMY_FILE_SCAN_INTERVAL')) or 5  # seconds

DEFAULT_TOLERANCE = 70  # meters
known_locations = {}

##########
#  CODE  #
##########

cache_file_location = os.path.expanduser('~') + '/Library/Caches/com.apple.findmy.fmipcore/'
cache_file_location_items = cache_file_location + 'Items.data'
cache_file_location_devices = cache_file_location + 'Devices.data'

device_updates = {}

client = mqtt.Client("ha-client")
client.username_pw_set(MQTT_CLIENT_USERNAME, MQTT_CLIENT_PASSWORD)
client.connect(host=MQTT_BROKER_IP, port=MQTT_BROKER_PORT)
client.loop_start()


def get_time(timestamp):
    if (type(timestamp) is not int):
        return "unknown"
    return str(datetime.fromtimestamp(timestamp / 1000))


def get_lat_lng_approx(meters):
    return meters / 111111


def load_data(data_file):
    with open(data_file, 'r') as f:
        data = json.load(f)
        f.close()
        return data


def get_device_id(name):
    return unidecode(re.sub(r'[\s-]', '_', name).lower())


def get_source_type(apple_position_type):
    switcher = {
        "crowdsourced": "gps",  # ble only used for stationary ble trackers
        "safeLocation": "gps",
        "Wifi": "router"
    }
    return switcher.get(apple_position_type, "gps")


def get_location_name(pos):
    for name, location in known_locations.items():
        tolerance = get_lat_lng_approx(location['tolerance'] or DEFAULT_TOLERANCE)
        if (math.isclose(location['latitude'], pos[0], abs_tol=tolerance) and
                math.isclose(location['longitude'], pos[1], abs_tol=tolerance)):
            return name
    return "not_home"


def send_data_items(forcesync):
    for device in load_data(cache_file_location_items):
        device_name = device['name']
        battery_status = device['batteryStatus']
        source_type = get_source_type(device.get('location').get('positionType') if device.get('location') else None)

        location_name = address = latitude = longitude = accuracy = lastUpdate = "unknown"
        if device['location'] is not None:
            latitude = device['location']['latitude']
            longitude = device['location']['longitude']
            address = device['address']
            accuracy = math.sqrt(
                device['location']['horizontalAccuracy'] ** 2 + device['location']['verticalAccuracy'] ** 2)
            location_name = get_location_name((latitude, longitude))
            lastUpdate = device['location']['timeStamp']

        device_update = device_updates.get(device_name)
        if not forcesync and device_update and len(device_update) > 0 and device_update[0] == lastUpdate:
            continue

        device_updates[device_name] = (lastUpdate, location_name)

        device_id = get_device_id(device_name)
        device_topic = f"homeassistant/device_tracker/{device_id}/"
        device_config = {
            "unique_id": device_id,
            "state_topic": device_topic + "state",
            "json_attributes_topic": device_topic + "attributes",
            "device": {
                "identifiers": device_id,
                "manufacturer": "Apple",
                "name": device_name
            },
            "source_type": source_type,
            "payload_home": "home",
            "payload_not_home": "not_home"
        }
        device_attributes = {
            "latitude": latitude,
            "longitude": longitude,
            "gps_accuracy": accuracy,
            "address": address,
            "batteryStatus": battery_status,
            "last_update_timestamp": lastUpdate,
            "last_update": get_time(lastUpdate),
            "provider": "FindMy (muehlt/home-assistant-findmy)"
        }

        client.publish(device_topic + "config", json.dumps(device_config))
        client.publish(device_topic + "attributes", json.dumps(device_attributes))
        client.publish(device_topic + "state", location_name)


def send_data_devices(forcesync):
    for device in load_data(cache_file_location_devices):
        device_name = device['name']
        battery_status = device['batteryStatus']
        battery_sevel = device['batteryLevel']
        source_type = get_source_type(device.get('location').get('positionType') if device.get('location') else None)

        location_name = address = latitude = longitude = accuracy = lastUpdate = "unknown"
        if device['location'] is not None:
            latitude = device['location']['latitude']
            longitude = device['location']['longitude']
            address = device['address']
            accuracy = math.sqrt(
                device['location']['horizontalAccuracy'] ** 2 + device['location']['verticalAccuracy'] ** 2)
            location_name = get_location_name((latitude, longitude))
            lastUpdate = device['location']['timeStamp']

        device_update = device_updates.get(device_name)
        if not forcesync and device_update and len(device_update) > 0 and device_update[0] == lastUpdate:
            continue

        device_updates[device_name] = (lastUpdate, location_name)

        device_id = get_device_id(device_name)
        device_topic = f"homeassistant/device_tracker/{device_id}/"
        device_config = {
            "unique_id": device_id,
            "state_topic": device_topic + "state",
            "json_attributes_topic": device_topic + "attributes",
            "device": {
                "identifiers": device_id,
                "manufacturer": "Apple",
                "name": device_name
            },
            "source_type": source_type,
            "payload_home": "home",
            "payload_not_home": "not_home"
        }
        device_attributes = {
            "latitude": latitude,
            "longitude": longitude,
            "gps_accuracy": accuracy,
            "address": address,
            "battery_status": battery_status,
            "battery_level": battery_sevel,
            "last_update_timestamp": lastUpdate,
            "last_update": get_time(lastUpdate),
            "provider": "FindMy (muehlt/home-assistant-findmy)"
        }

        client.publish(device_topic + "config", json.dumps(device_config))
        client.publish(device_topic + "attributes", json.dumps(device_attributes))
        client.publish(device_topic + "state", location_name)


def scan_cache(privacy, forcesync):
    console = Console()
    with console.status(f"[bold green]Synchronizing {len(device_updates)} devices and {len(known_locations)} known locations") as status:
        while True:
            send_data_items(forcesync)
            send_data_devices(forcesync)

            os.system('clear')

            if not privacy:
                device_table = Table()
                device_table.add_column("Device")
                device_table.add_column("Last Update")
                device_table.add_column("Location")
                for device, details in sorted(device_updates.items(), key=lambda x: get_time(x[1][0])):
                    device_table.add_row(device, get_time(details[0]), details[1])
                console.print(device_table)

            status.update(f"[bold green]Synchronizing {len(device_updates)} devices and {len(known_locations)} known locations")

            time.sleep(FINDMY_FILE_SCAN_INTERVAL)


def validate_param_locations(_, __, path):
    if path is None:
        raise click.BadParameter('Please provide a valid path to the known locations config file.')

    if not os.path.isfile(path):
        raise click.BadParameter('The provided path is not a file.')

    with open(path, 'r') as f:
        try:
            locations = json.load(f)
        except json.JSONDecodeError:
            raise click.BadParameter('The provided file does not contain valid JSON data.')

    if not isinstance(locations, dict):
        raise click.BadParameter('The provided file does not contain a valid JSON object.')

    for name, location in locations.items():
        if not isinstance(name, str):
            raise click.BadParameter(f'The location name "{name}" is not a string.')
        if not isinstance(location, dict):
            raise click.BadParameter(f'The location "{name}" is not a valid JSON object.')
        if not isinstance(location.get('latitude'), float):
            raise click.BadParameter(f'The location "{name}" does not contain a valid latitude.')
        if not isinstance(location.get('longitude'), float):
            raise click.BadParameter(f'The location "{name}" does not contain a valid longitude.')
        if not isinstance(location.get('tolerance'), int):
            raise click.BadParameter(f'The location "{name}" does not contain a valid tolerance in meters.')

    return path, locations


def set_known_locations(locations):
    global known_locations
    _path, _known_locations = locations
    known_locations = _known_locations


@click.command()
@click.option('--locations', '-l', callback=validate_param_locations, help='Path to the known locations JSON configuration file')
@click.option('--privacy', '-p', is_flag=True, help='Hides specific device data from the console output')
@click.option('--forcesync', '-f', is_flag=True, help='Disables the timestamp check and provides and update every FINDMY_FILE_SCAN_INTERVAL seconds')
def main(locations, privacy, forcesync):
    set_known_locations(locations)
    scan_cache(privacy, forcesync)


if __name__ == '__main__':
    main()
