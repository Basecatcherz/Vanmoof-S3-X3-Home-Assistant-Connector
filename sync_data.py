import asyncio
import bleak
from pymoof.clients.sx3 import SX3Client
import paho.mqtt.publish as mqtt
import time
import json

# --- Configuration ---
MAX_BATTERY_CHECKS = 3
RETRY_DELAY_SECONDS = 5
MQTT_HOSTNAME = "127.0.0.1" # MQTT Server
MQTT_PORT = 1883 ' MQTT Port
MQTT_BASE_TOPIC = "homeassistant/sensor/vanmoof_s3"
MQTT_STATE_TOPIC = f"{MQTT_BASE_TOPIC}/state"
MQTT_PRESENCE_TOPIC = f"{MQTT_BASE_TOPIC}/presence"
MQTT_AVAILABILITY_TOPIC = f"{MQTT_BASE_TOPIC}/availability"
MQTT_AUTH = {"username": "YOUR_MQTT_USER", "password": "YOUR_MQTT_PASSWORD"} # MQTT Credentials
BIKE_MAC_ADDRESS = 'XX:XX:XX:XX:XX:XX' # Bike's MAC adress
BIKE_ENCRYPTION_KEY = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx' # Encryption key
BIKE_USER_KEY_ID = 1 # User key id
BIKE_NAME = "VanMoof S3"
DEVICE_ID = "vanmoof_s3_bike"
# --- End Configuration ---


def publish_discovery(sensor_id, name, unit, device_class, value_template, topic, unique_id_suffix):
    """
    Publishes a Home Assistant MQTT discovery config for a sensor.
    """
    config_topic = f"homeassistant/sensor/{DEVICE_ID}/{sensor_id}/config"
    payload = {
        "name": name,
        "state_topic": topic,
        "unit_of_measurement": unit,
        "device_class": device_class,
        "value_template": value_template,
        "unique_id": f"{DEVICE_ID}_{unique_id_suffix}",
        "device": {
            "identifiers": [DEVICE_ID],
            "name": BIKE_NAME,
            "manufacturer": "VanMoof",
            "model": "S3",
        },
        "availability_topic": MQTT_AVAILABILITY_TOPIC,
        "payload_available": "online",
        "payload_not_available": "offline"
    }
    mqtt.single(
        topic=config_topic,
        payload=json.dumps(payload),
        hostname=MQTT_HOSTNAME,
        port=MQTT_PORT,
        auth=MQTT_AUTH,
        retain=True
    )


def publish_discovery_binary(sensor_id, name, value_template, topic, unique_id_suffix):
    """
    Publishes a Home Assistant MQTT discovery config for a binary sensor (e.g. presence).
    """
    config_topic = f"homeassistant/binary_sensor/{DEVICE_ID}/{sensor_id}/config"
    payload = {
        "name": name,
        "state_topic": topic,
        "device_class": "presence",
        "value_template": value_template,
        "unique_id": f"{DEVICE_ID}_{unique_id_suffix}",
        "device": {
            "identifiers": [DEVICE_ID],
            "name": BIKE_NAME,
            "manufacturer": "VanMoof",
            "model": "S3",
        }
    }
    mqtt.single(
        topic=config_topic,
        payload=json.dumps(payload),
        hostname=MQTT_HOSTNAME,
        port=MQTT_PORT,
        auth=MQTT_AUTH,
        retain=True
    )

def publish_discovery_lock(sensor_id, name, value_template, topic, unique_id_suffix):
    """
    Publishes a Home Assistant MQTT discovery config for the lock binary sensor.
    """
    config_topic = f"homeassistant/binary_sensor/{DEVICE_ID}/{sensor_id}/config"
    payload = {
        "name": name,
        "state_topic": topic,
        "device_class": "lock",
        "payload_on": "OFF",
        "payload_off": "ON",
        "value_template": value_template,
        "unique_id": f"{DEVICE_ID}_{unique_id_suffix}",
        "device": {
            "identifiers": [DEVICE_ID],
            "name": BIKE_NAME,
            "manufacturer": "VanMoof",
            "model": "S3",
        },
        "availability_topic": MQTT_AVAILABILITY_TOPIC,
        "payload_available": "online",
        "payload_not_available": "offline"
    }
    mqtt.single(
        topic=config_topic,
        payload=json.dumps(payload),
        hostname=MQTT_HOSTNAME,
        port=MQTT_PORT,
        auth=MQTT_AUTH,
        retain=True
    )


def publish_ha_autodiscovery():
    """
    Sends all necessary MQTT discovery messages for Home Assistant.
    """
    print("Publishing Home Assistant MQTT discovery configs...")

    # Battery Sensor
    publish_discovery(
        sensor_id="battery",
        name="VanMoof S3 Battery",
        unit="%",
        device_class="battery",
        value_template="{{ value_json.battery }}",
        topic=MQTT_STATE_TOPIC,
        unique_id_suffix="battery"
    )

    # Distance Sensor
    publish_discovery(
        sensor_id="distance",
        name="VanMoof S3 Distance",
        unit="km",
        device_class="distance",
        value_template="{{ value_json.distance }}",
        topic=MQTT_STATE_TOPIC,
        unique_id_suffix="distance"
    )

    # Presence Binary Sensor
    publish_discovery_binary(
        sensor_id="presence",
        name="VanMoof S3 Presence",
        value_template="{{ value_json.present }}",
        topic=MQTT_PRESENCE_TOPIC,
        unique_id_suffix="presence"
    )

    # Lock Binary Sensor
    publish_discovery_lock(
        sensor_id="lock",
        name="VanMoof S3 Lock",
        value_template="{{ value_json.lock_status }}",
        topic=MQTT_STATE_TOPIC,
        unique_id_suffix="lock"
    )

# Check for the BLE device presence
async def check_ble_presence(mac_address: str, timeout: int = 5) -> bool:
    print(f"Scanning for BLE device {mac_address}...")
    devices = await bleak.BleakScanner.discover(timeout=timeout)
    for d in devices:
        if d.address.upper() == mac_address.upper():
            print("VanMoof detected nearby.")
            return True
    print("VanMoof not found.")
    return False

# Check current battery level including workaround for firmware issues causing random reports of 100% charge
async def get_stable_battery_level(client: SX3Client) -> int:
    print("Performing initial battery level check...")
    batterylevel = await client.get_battery_level()
    print(f"Initial check result: {batterylevel}%")

    if batterylevel == 100:
        print("Battery level reported as 100%. Starting re-checks...")
        for i in range(MAX_BATTERY_CHECKS - 1):
            attempt_num = i + 2
            print(f"Waiting {RETRY_DELAY_SECONDS} seconds before attempt #{attempt_num}...")
            await asyncio.sleep(RETRY_DELAY_SECONDS)
            print(f"Re-checking battery level (Attempt #{attempt_num})...")
            current_check = await client.get_battery_level()
            print(f"Attempt #{attempt_num} result: {current_check}%")
            if current_check < 100:
                batterylevel = current_check
                print(f"Detected non-100% level ({batterylevel}%) on attempt #{attempt_num}. Using this value.")
                break
    return batterylevel


async def run_bike_check():
    # Publish Home Assistant Discovery Topics (before sending states)
    publish_ha_autodiscovery()

    device = BIKE_MAC_ADDRESS
    key = BIKE_ENCRYPTION_KEY
    user_key_id = BIKE_USER_KEY_ID

    present = await check_ble_presence(device)
    availability_payload = "online" if present else "offline"

    print(f"Publishing availability to MQTT: {availability_payload}")
    try:
        mqtt.single(
            topic=MQTT_AVAILABILITY_TOPIC,
            payload=availability_payload,
            hostname=MQTT_HOSTNAME,
            port=MQTT_PORT,
            auth=MQTT_AUTH
        )
    except Exception as e:
        print(f"Error sending availability via MQTT: {e}")

    print(f"Publishing presence state to MQTT: {present}")
    try:
        mqtt.single(
            topic=MQTT_PRESENCE_TOPIC,
            payload=json.dumps({"present": "ON" if present else "OFF"}),
            hostname=MQTT_HOSTNAME,
            port=MQTT_PORT,
            auth=MQTT_AUTH
        )
    except Exception as e:
        print(f"Error sending presence via MQTT: {e}")

    if not present:
        print("Bike is not present. All dependent sensors are set to 'unavailable'. Aborting data check.")
        return

    print(f"Attempting to connect to bike: {device}")
    try:
        async with bleak.BleakClient(device) as bleak_client:
            print("Connected to BLE device. Authenticating...")
            client = SX3Client(bleak_client, key, user_key_id)
            await client.authenticate()
            print("Authentication successful.")

            final_batterylevel = await get_stable_battery_level(client)
            
            print("Checking distance travelled...")
            distancedriven = await client.get_distance_travelled()

            print("Checking lock status...")
            lock_status = await client.get_lock_state()
            lock_status_str = "ON" if str(lock_status) == "LockState.LOCKED" else "OFF"
            print(f"Lock State: {lock_status}")
            print(f"Lock status is: {lock_status_str}")

            payload = {
                "battery": final_batterylevel,
                "distance": distancedriven,
                "lock_status": lock_status_str
            }

            print(f"Sending data to MQTT: {payload}")
            try:
                mqtt.single(
                    topic=MQTT_STATE_TOPIC,
                    payload=json.dumps(payload),
                    hostname=MQTT_HOSTNAME,
                    port=MQTT_PORT,
                    auth=MQTT_AUTH
                )
                print("MQTT data sent successfully.")
            except Exception as e:
                print(f"Error sending data via MQTT: {e}")

    except bleak.BleakError as e:
        print(f"Bluetooth connection error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    print("Starting VanMoof S3 presence + data check (with Home Assistant support)...")
    asyncio.run(run_bike_check())
    print("Script finished.")
