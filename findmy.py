#!/usr/bin/python3

# .                                       .           .                   .          
# |                                 o     |           |        ,- o       |          
# |-. ,-. ;-.-. ,-. --- ,-: ,-. ,-. . ,-. |-  ,-: ;-. |-  ---  |  . ;-. ,-| ;-.-. . .
# | | | | | | | |-'     | | `-. `-. | `-. |   | | | | |        |- | | | | | | | | | |
# ' ' `-' ' ' ' `-'     `-` `-' `-' ' `-' `-' `-` ' ' `-'      |  ' ' ' `-' ' ' ' `-|
#                                                             -'                  `-'
# made with ♡ by muehlt
# github.com/muehlt
# version 0.0.1
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

from datetime import datetime
import math
import re
import time
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import os 
import json
from halo import Halo
from unidecode import unidecode
from dotenv import load_dotenv 
load_dotenv()

###################
#  CONFIGURATION  #
###################

BROKER_IP = '192.168.178.5'
BROKER_PORT = 1883
MQTT_USER_NAME = 'mqtt_client'
MQTT_USER_PASSWORD = os.environ.get('MQTT_PASSWORD') # use an environment variable to store the password
REFRESH_INTERVAL = 5 # seconds

# Apple's "Safe Locations" don't seem to be very reliable, so you can define a
# list of known locations that will be used instead. If none matches, 'not_home'
# will be sent to Home Assistant. If coordinates overlap, the first match will be returned.
# 'name': (latitude, longitude, tolerance in meters [approximation])
DEFAULT_TOLERANCE = 70 # in meters (approximation)
KNOWN_LOCATIONS = {
    'home': (12.3456789, 12.3456789, DEFAULT_TOLERANCE),
    'work': (12.3456789, 12.3456789, DEFAULT_TOLERANCE),
}




##########
#  CODE  #
##########

cache_file_location = os.path.expanduser('~') + '/Library/Caches/com.apple.findmy.fmipcore/'
cache_file_location_items = cache_file_location + 'Items.data'
cache_file_location_devices = cache_file_location + 'Devices.data'

device_updates = {}

spinner = Halo(text='Syncing FindMy data ...', spinner='dots')
spinner.start()

client = mqtt.Client("ha-client")
client.username_pw_set(MQTT_USER_NAME, MQTT_USER_PASSWORD)
client.connect(host=BROKER_IP, port=BROKER_PORT)
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
        "crowdsourced": "gps", # ble only used for stationary ble trackers
        "safeLocation": "gps",
        "Wifi": "router"
    }
    return switcher.get(apple_position_type, "gps")

def get_location_name(pos):
    for name, location in KNOWN_LOCATIONS.items():
        tolerance = get_lat_lng_approx(location[2])
        if math.isclose(location[0], pos[0], abs_tol=tolerance) and math.isclose(location[1], pos[1], abs_tol=tolerance):
            return name
    return "not_home"

def send_data_items():
    for device in load_data(cache_file_location_items):
        device_name = device['name']        
        battery_status = device['batteryStatus']
        source_type = get_source_type(device.get('location').get('positionType') if device.get('location') else None)

        location_name = address = latitude = longitude = accuracy = lastUpdate = "unknown"
        if device['location'] is not None:
            latitude = device['location']['latitude']
            longitude = device['location']['longitude']
            address = device['address']
            accuracy = math.sqrt(device['location']['horizontalAccuracy'] **2 + device['location']['verticalAccuracy'] **2)
            location_name = get_location_name((latitude, longitude))
            lastUpdate = device['location']['timeStamp']

        device_updates[device_name] = lastUpdate

        device_id = get_device_id(device_name)
        device_topic = f"homeassistant/device_tracker/{device_id}/"
        device_config = {
            "name": device_name,
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

def send_data_devices():
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
            accuracy = math.sqrt(device['location']['horizontalAccuracy'] **2 + device['location']['verticalAccuracy'] **2)
            location_name = get_location_name((latitude, longitude))
            lastUpdate = device['location']['timeStamp']

        device_updates[device_name] = lastUpdate

        device_id = get_device_id(device_name)
        device_topic = f"homeassistant/device_tracker/{device_id}/"
        device_config = {
            "name": device_name,
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

while True:
    send_data_items()
    send_data_devices()

    os.system('clear')
    for device in device_updates:
        print(f"{device}: {get_time(device_updates[device])}")
    time.sleep(REFRESH_INTERVAL)