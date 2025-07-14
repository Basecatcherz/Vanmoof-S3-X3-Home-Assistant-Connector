# Vanmoof S3 / X3 Home Assistant Connector
A Python script that connects a Vanmoof S3 or X3 to Home Assistant using [Pymoof](https://github.com/quantsini/pymoof/) and MQTT.

## What does it do?
This Python script will connect to a Vanmoof S3 or X3 and send the following data to a MQTT broker:
- Availability
- Battery level
- Distance driven
- Lock state

The script also publishes auto discovery messages to make sure the bike will show up in Home Assistant automatically.

## Requirements
- Bluetooth LE enabled device to run the script on (tested on Raspberry Pi 3)
- Home Assistant
- MQTT Broker

## Installation
1. Create a new Python venv
2. Install dependencies
	- [pymoof](https://github.com/quantsini/pymoof/)
 	- [paho-mqtt](https://pypi.org/project/paho-mqtt/)
  	- [bleak](https://pypi.org/project/bleak/)
3. Edit script
   - MQTT Server
   - Bike's MAC address
   - Credentials
4. Run the script periodically (e.g. via cron)
