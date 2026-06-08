import time
import requests
import io
import numpy as np
from picamera2 import Picamera2
from picamera2.devices import IMX500
from picamera2.devices.imx500 import NetworkIntrinsics
from PIL import Image

# --- CONFIGURAZIONI ---
NODE_RED_URL = "http://127.0.0.1:1880/person-detected"
COOLDOWN_SECONDS = 15.0
CONFIDENCE_THRESHOLD = 0.6

last_alert_time = 0
last_detections = []  # <-- variabile globale usata da parse_detections

# --- 1. CARICA IL MODELLO ---
imx500 = IMX500("/usr/share/imx500-models/imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk")

# --- 2. CONFIGURA GLI INTRINSICS (metadati del modello) ---
intrinsics = imx500.network_intrinsics
if not intrinsics:
    intrinsics = NetworkIntrinsics()
    intrinsics.task = "object detection"
intrinsics.update_with_defaults()

# --- 3. INIZIALIZZA LA TELECAMERA ---
picam2 = Picamera2(imx500.camera_num)
camera_config = picam2.create_preview_configuration(
    main={"size": (1024, 768)},
    lores={"size": (640, 480)}
)
picam2.configure(camera_config)
picam2.start()

# --- 4. CLASSE E FUNZIONE DI PARSING (devono stare DOPO imx500 e picam2) ---
class Detection:
    def __init__(self, coords, category, conf, metadata):
        self.category = category
        self.conf = conf
        self.box = imx500.convert_inference_coords(coords, metadata, picam2)

def parse_detections(metadata: dict):
    global last_detections
    np_outputs = imx500.get_outputs(metadata, add_batch=True)
    if np_outputs is None:
        return last_detections  # ritorna l'ultimo risultato valido se il tensore non è pronto

    boxes, scores, classes = np_outputs[0][0], np_outputs[1][0], np_outputs[2][0]
    detections = []
    for box, score, category in zip(boxes, scores, classes):
        if score > CONFIDENCE_THRESHOLD:
            label = intrinsics.labels[int(category)] if intrinsics.labels else str(int(category))
            detections.append(Detection(box, label, float(score), metadata))
    last_detections = detections
    return detections

# --- 5. LOOP PRINCIPALE ---
print("Telecamera avviata, rilevamento persone in corso...")

try:
    while True:
        request = picam2.capture_request()
        metadata = request.get_metadata()
        request.release()  # <-- importante: libera il buffer subito dopo

        detections = parse_detections(metadata)

        person_detected = False
        confidence_score = 0.0

        for obj in detections:
            if obj.category == "person" and obj.conf > CONFIDENCE_THRESHOLD:
                person_detected = True
                confidence_score = obj.conf
                break

        if person_detected:
            current_time = time.time()
            if (current_time - last_alert_time) > COOLDOWN_SECONDS:
                print(f"[{time.strftime('%H:%M:%S')}] Persona rilevata ({confidence_score:.2f})! Cattura foto...")

                jpeg_stream = io.BytesIO()

                # picam2.capture_file(jpeg_stream, format="jpeg")

                # cattura come array per comprimere maggiormente il file
                array = picam2.capture_array("main")
                img = Image.fromarray(array).convert("RGB")
                img.save(jpeg_stream, format="jpeg", quality=60)

                jpeg_stream.seek(0)

                files = {'image': ('detection.jpg', jpeg_stream, 'image/jpeg')}
                data = {
                    "event": "person_detected",
                    "confidence": str(confidence_score),
                    "device": "AI-Camera"
                }

                print("Invio del Blob JPEG a Node-RED...")
                try:
                    response = requests.post(NODE_RED_URL, files=files, data=data, timeout=5)
                    if response.status_code == 200:
                        print("Foto e dati inviati con successo!")
                except requests.exceptions.RequestException as e:
                    print(f"Errore durante l'invio a Node-RED: {e}")

                last_alert_time = current_time

        time.sleep(1)

except KeyboardInterrupt:
    print("\nChiusura dello script...")
finally:
    picam2.stop()