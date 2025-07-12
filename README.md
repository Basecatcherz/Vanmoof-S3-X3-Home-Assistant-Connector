
# Vanmoof S3 / X3 Home Assistant Connector
A Python script that connects a Vanmoof S3 or X3 to Home Assistant using Pymoof and MQTT.

## What does this do?
This Python script will connect to a Vanmoof S3 or X3 and send the following data to a MQTT broker:
- Availability
- Battery level
- Distance driven
- Lock state

## Requirements
- Bluetooth LE enabled device to run the script on (tested on Raspberry Pi 3)
- Home Assistant
- MQTT Broker

## Installation
1. Create a new Python venv
2. Install dependencies
3. Edit script
   - MQTT Server
   - Bike's MAC address
   - Credentials
5. Run the script periodically (e.g. via cron)
