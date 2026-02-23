# api_to_pico.py
import serial
import requests
import time

SERIAL_PORT = "COM3"   # pas aan
API_URL = "http://localhost:5000/status"

ser = serial.Serial(SERIAL_PORT, 115200)

while True:
    try:
        response = requests.get(API_URL)
        data = response.json()
        level = int(data["defcon"])

        print("DEFCON:", level)
        ser.write(f"{level}\n".encode())

    except Exception as e:
        print("Fout:", e)

    time.sleep(5)
