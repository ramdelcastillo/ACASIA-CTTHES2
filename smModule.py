import json
import os
import threading
import time
import paho.mqtt.client as mqtt
import os
import msvcrt


BROKER = "192.168.109.155"
PORT = 1883
TOPIC = "logs/new"
USERNAME = "testuser"
PASSWORD = "testpass"

LOG_FILE = r"C:\Shared\save_simplified_broker.json"
STATUS_FILE = r"C:\Shared\checkDone.json"

DEFAULT_TIMEOUT = 2
OPEN_TIMEOUT = 3

LAST_LOG_TIME = time.time()
CURRENT_TIMEOUT = DEFAULT_TIMEOUT
lock = threading.Lock()

if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w") as f:
        json.dump([], f)


def updateStatus(status_value):
    for _ in range(5):  # Retry up to 5 times
        try:
            with open(STATUS_FILE, "w") as f:
                json.dump({"status": status_value}, f)
            os.replace(STATUS_FILE, STATUS_FILE)  # Ensures atomic replacement
            return
        except PermissionError as e:
            if e.winerror == 32:
                print("File is in use, retrying...")
                time.sleep(0.1)  # Wait before retrying
            else:
                raise  # Raise other errors


def checkTimeout():
    global LAST_LOG_TIME, CURRENT_TIMEOUT
    while True:
        time.sleep(1)
        with lock:
            TIME_SINCE_LAST_LOG = time.time() - LAST_LOG_TIME
            if TIME_SINCE_LAST_LOG >= CURRENT_TIMEOUT:
                try:
                    with open(STATUS_FILE, "r") as f:
                        CURRENT_STATUS = json.load(f).get("status", "waiting")
                except (json.JSONDecodeError, FileNotFoundError) as e:
                    print(f"Error reading status file: {e}")
                    CURRENT_STATUS = "waiting"  # Default fallback

                if CURRENT_STATUS == "receiving":
                    updateStatus("done")
                    print(f"No logs received for {CURRENT_TIMEOUT} sec. Setting status to 'done'.")



def serverParsing(msg_payload):
    try:
        NEW_LOG = json.loads(msg_payload)
        print(f"Received log: {NEW_LOG}")

        with open(LOG_FILE, "r") as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                logs = []

        logs.append(NEW_LOG)

        with open(LOG_FILE, "w") as f:
            json.dump(logs, f, indent=4)

        return NEW_LOG
    except json.JSONDecodeError:
        print("Received invalid JSON!")
        return None


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker")
        client.subscribe(TOPIC)
        print(f"Subscribed to '{TOPIC}'")
    else:
        print(f"Failed to connect, return code {rc}")


def on_message(client, userdata, msg):
    global LAST_LOG_TIME, CURRENT_TIMEOUT
    PARSED_LOG = serverParsing(msg.payload.decode())
    if PARSED_LOG:
        with lock:
            LAST_LOG_TIME = time.time()
            FILE_ACCESS_TYPE = PARSED_LOG.get("fileAccessType", "")
            CURRENT_TIMEOUT = OPEN_TIMEOUT if FILE_ACCESS_TYPE == "File Opening" else DEFAULT_TIMEOUT
            updateStatus("receiving")
            print(f"Log received. Timeout reset to {CURRENT_TIMEOUT} sec.")


def on_disconnect(client, userdata, rc):
    print("Disconnected from broker.")
    if rc != 0:
        print("Unexpected disconnection. Attempting to reconnect...")
        for i in range(5):
            try:
                time.sleep(3)
                client.reconnect()
                print("Reconnected successfully")
                return
            except Exception as e:
                print(f"Reconnect attempt {i + 1} failed: {e}")
        print("Failed to reconnect. Shutting down.")


client = mqtt.Client()
client.username_pw_set(USERNAME, PASSWORD)
client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect

threading.Thread(target=checkTimeout, daemon=True).start()

try:
    client.connect(BROKER, PORT)
    client.loop_forever()
except Exception as e:
    print(f"Connection error: {e}")
