import paho.mqtt.client as mqtt
import json
import time
import os

# Messaging Module
# Runs on its own - waits for simplified logs to send to Broker VM

BROKER = "192.168.109.155"
PORT = 1883
TOPIC = "logs/new"
USERNAME = "testuser"
PASSWORD = "testpass"

LOG_FILE = r"C:\Shared\save_simplified.json"

client = mqtt.Client()
client.username_pw_set(USERNAME, PASSWORD)
client.connect(BROKER, PORT)
client.loop_start()

last_processed_length = 0

def read_new_logs():
    global last_processed_length
    if not os.path.exists(LOG_FILE):
        return []

    with open(LOG_FILE, "r") as f:
        try:
            logs = json.load(f)
            new_entries = logs[last_processed_length:]
            last_processed_length = len(logs)
            return new_entries
        except json.JSONDecodeError:
            return []


def publish_logs():
    while True:
        new_logs = read_new_logs()
        for log in new_logs:
            json_message = json.dumps(log)
            print(f"Sending log: {json_message}")
            client.publish(TOPIC, json_message, qos=1)

        time.sleep(1)

try:
    publish_logs()
except KeyboardInterrupt:
    print("Stopping publisher...")
    client.loop_stop()
    client.disconnect()