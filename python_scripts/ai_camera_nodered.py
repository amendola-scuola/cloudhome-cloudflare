import time
import requests
import io
from picamera2 import Picamera2

# --- CONFIGURAZIONI ---
NODE_RED_URL = "http://127.0.0.1:1880/person-detected"
COOLDOWN_SECONDS = 8.0  # Tempo di attesa tra una notifica e l'altra

last_alert_time = 0

# Inizializza Picamera2
picam2 = Picamera2()

# Configurazione a DOPPIO FLUSSO:
# 'main' per lo scatto in alta definizione, 'lores' per il chip AI
camera_config = picam2.create_preview_configuration(
    main={"size": (1280, 720)},  # Alta risoluzione per la foto
    lores={"size": (640, 480)}    # Bassa risoluzione per l'algoritmo AI
)
picam2.configure(camera_config)
picam2.start()

print("Telecamera avviata in modalità doppio flusso (HD + AI). In attesa...")

try:
    while True:
        # Cattura i metadati dal flusso a bassa risoluzione
        request = picam2.capture_request()
        metadata = request.get_metadata()
        
        # Recupera i rilevamenti dell'hardware IMX500
        detections = metadata.get("Imx500ObjectDetection", [])
        
        person_detected = False
        confidence_score = 0.0
        
        for obj in detections:
            if obj.get("label") == "person" and obj.get("confidence", 0) > 0.6:
                person_detected = True
                confidence_score = obj.get("confidence")
                break
        
        # Se viene rilevata una persona e il cooldown è passato
        if person_detected:
            current_time = time.time()
            if (current_time - last_alert_time) > COOLDOWN_SECONDS:
                print(f"[{time.strftime('%H:%M:%S')}] Persona rilevata ({confidence_score:.2f})! Cattura foto HD...")
                
                # 1. Cattura lo scatto ad alta risoluzione in memoria (formato JPEG)
                jpeg_stream = io.BytesIO()
                picam2.capture_file(jpeg_stream, format="jpeg", encoder_options={})
                jpeg_stream.seek(0) # Riposiziona il puntatore all'inizio del file in memoria
                
                # 2. Prepara il file binario (Blob) e i metadati da inviare
                # 'files' simula l'invio di un form con un file allegato
                files = {
                    'image': ('detection.jpg', jpeg_stream, 'image/jpeg')
                }
                # Dati testuali opzionali da allegare insieme alla foto
                data = {
                    "event": "person_detected",
                    "confidence": str(confidence_score),
                    "device": "Raspberry Pi 5 - AI Camera HD"
                }
                
                # 3. Invia il tutto a Node-RED tramite POST multipart
                print("Invio del Blob JPEG a Node-RED...")
                try:
                    response = requests.post(NODE_RED_URL, files=files, data=data, timeout=5)
                    if response.status_code == 200:
                        print("Foto e dati inviati con successo!")
                except requests.exceptions.RequestException as e:
                    print(f"Errore durante l'invio a Node-RED: {e}")
                
                last_alert_time = current_time
                
except KeyboardInterrupt:
    print("\nChiusura dello script...")
finally:
    picam2.stop()