print("YO getting started babe")
import os
import mlflow
import paho.mqtt.client as mqtt
from dotenv import load_dotenv
import base64  # if snapshots come base64-encoded in events topic
import cv2
import numpy as np
# ... your other imports (e.g., torch, transformers pipe, etc.)

import sys
import datetime

# Force flush just in case
sys.stdout.flush()

print(f"[{datetime.datetime.now()}] >>> DETECTION1 CONTAINER STARTED <<<")
print(f"[{datetime.datetime.now()}] Python version: {sys.version}")
print(f"[{datetime.datetime.now()}] Attempting MQTT connection to mosquitto.mqtt.svc.cluster.local:1883...")
sys.stdout.flush()


load_dotenv()  # For local dev; in k8s use Secrets

# MLflow setup
mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://mlflow-service.mlflow.svc.cluster.local:5000"))
mlflow.set_experiment("detection-experiments")

# MQTT credentials (from Secrets in k8s)
MQTT_BROKER = os.getenv("MQTT_BROKER", "mqtt-broker.default.svc.cluster.local")  # adjust to your broker service
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_USER = os.getenv("MQTT_USER")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
MQTT_TOPIC = "frigate/#"
#MQTT_TOPIC = "frigate/+/snapshot"

# Your inference pipeline (example placeholder)
# pipe = SomeModel(...)

def process_image(image_bytes: bytes):
    """Run your CV / gen / TTS pipeline here."""
    # Decode JPEG
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # ... your inference: generated_img, text, audio, etc.
    inference_time = 12.5  # replace with actual timing
    generated_path = "/data/generated.jpg"  # PVC mount
    cv2.imwrite(generated_path, img)  # example artifact
    
    return inference_time, generated_path

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker")
        client.subscribe(MQTT_TOPIC)
        print(f"Subscribed to {MQTT_TOPIC}")
    else:
        print(f"Connection failed with code {rc}")

def on_message(client, userdata, msg):
    print(f"[{datetime.datetime.now()}] >>> RAW MQTT MESSAGE RECEIVED <<<")
    print(f"Topic: {msg.topic}")
    print(f"Payload length: {len(msg.payload)} bytes")
    print(f"Payload type: {type(msg.payload)}")
    print(f"First 50 bytes (hex): {msg.payload[:50].hex()}")
    sys.stdout.flush()  # Force it out
    
    if not msg.topic.endswith('snapshot'):
        return

    with mlflow.start_run(run_name="detection-run"):
        mlflow.log_param("topic", msg.topic)
        mlflow.log_param("prompt", "cyberpunk style")  # or dynamic
        
        # Handle payload: raw JPEG on snapshot topics
        image_bytes = msg.payload
        # If using frigate/events topic instead, it's base64: 
        # payload = json.loads(msg.payload)
        # image_bytes = base64.b64decode(payload["after"]["snapshot"])
        
        inference_time, artifact_path = process_image(image_bytes)
        
        mlflow.log_metric("inference_time", inference_time)
        mlflow.log_artifact(artifact_path)
        
        # Optional: trigger downstream actions (e.g., publish result back to MQTT)

# Create and configure the client
client = mqtt.Client(client_id="detection1")
if MQTT_USER and MQTT_PASSWORD:
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)

client.on_connect = on_connect
client.on_message = on_message

# Connect and loop
client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
client.loop_forever()  # Blocks here; handles reconnects automatically
