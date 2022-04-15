import time
import json
import yaml
import ltr559
import sys, os, pathlib
from grow.moisture import Moisture
import paho.mqtt.client as mqtt


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    print(client.subscribe(broker().get('topic')))


def on_message(client, userdata, msg):
    print(msg.topic + " " + str(msg.payload))


def load_config():

    pathlib.Path(__file__).parent.absolute()
    with open(os.path.join(pathlib.Path(__file__).parent.absolute(), 'local_config.yaml')) as f:
        return yaml.safe_load(f)


def broker():
    return load_config().get('broker')


def auth():
    return load_config().get('auth')

def generate_payload(light, sensors):
    i = 0
    payload = {"light": light.get_lux()}
    for i in range(0, len(sensors)):
        payload["sensor_{}".format(i)] = {
            "moisture": sensors[i].moisture,
            "saturation": sensors[i].saturation,
            "moisture_inv": 1/max(1, sensors[i].moisture),
        }
    return payload


config = load_config()
broker = broker()
auth = auth()

# Give time for the network to be initialised before starting up
print("Starting up")
time.sleep(config.get("startup_wait", 0))

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.username_pw_set(auth.get('username'), auth.get('password'))

print("Start submitting sensor data on MQTT topic {}".format(broker.get('topic')))

sensors = [
  Moisture(1, wet_point=1, dry_point=10),
  Moisture(2, wet_point=1, dry_point=10),
  Moisture(3, wet_point=1, dry_point=10),
]
light = ltr559.LTR559()

while True:

    payload = generate_payload(light, sensors)

    client.connect(broker.get('host', 'homeassistant.local'), broker.get('port', 1883), 60)

    pub = client.publish(broker.get('topic'), json.dumps(payload))

    pub.wait_for_publish()

    client.disconnect()

    print(json.dumps(payload))

    time.sleep(config.get("read_rate", 30))

client.loop_forever()
