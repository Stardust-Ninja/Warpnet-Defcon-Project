# code.py - WORKING VERSION met recv_into
import board
from digitalio import DigitalInOut, Direction
import wifi
import socketpool
import time
import json

WIFI_SSID = "881ifjAjnd"
WIFI_PASSWORD = "12345678"
API_HOST = "10.126.111.127"
API_PORT = 5000
SCAN_INTERVAL = 5

green = DigitalInOut(board.GP0)
blue = DigitalInOut(board.GP1)
yellow = DigitalInOut(board.GP2)
red = DigitalInOut(board.GP3)
white = DigitalInOut(board.GP4)

leds = [green, blue, yellow, red, white]

for led in leds:
    led.direction = Direction.OUTPUT
    led.value = False

current_level = 5
last_update = 0
blink_state = False
police_state = 0

def all_off():
    for led in leds:
        led.value = False

def all_on():
    for led in leds:
        led.value = True

def update_lights():
    global last_update, blink_state, police_state
    now = time.monotonic()
    
    if current_level == 5:
        all_off()
        green.value = True
    elif current_level == 4:
        if now - last_update > 0.6:
            blink_state = not blink_state
            last_update = now
        all_off()
        blue.value = blink_state
    elif current_level == 3:
        if now - last_update > 0.3:
            blink_state = not blink_state
            last_update = now
        all_off()
        yellow.value = blink_state
    elif current_level == 2:
        if now - last_update > 0.15:
            blink_state = not blink_state
            last_update = now
        all_off()
        red.value = blink_state
    elif current_level == 1:
        if now - last_update > 0.1:
            last_update = now
            police_state = (police_state + 1) % 4
        all_off()
        if police_state == 0 or police_state == 1:
            red.value = True
        else:
            white.value = True

def connect_wifi():
    print(f"Connecting to {WIFI_SSID}...")
    wifi.radio.connect(WIFI_SSID, WIFI_PASSWORD)
    ip = str(wifi.radio.ipv4_address)
    print(f"Connected! IP: {ip}")
    return ip

def fetch_api():
    print(f"Connecting to {API_HOST}:{API_PORT}...")
    
    try:
        pool = socketpool.SocketPool(wifi.radio)
        sock = pool.socket()
        sock.settimeout(5)
        sock.connect((API_HOST, API_PORT))
        
        request = f"GET /api/security/status HTTP/1.1\r\nHost: {API_HOST}\r\nConnection: close\r\n\r\n"
        sock.send(request.encode())
        
        # FIX: Gebruik recv_into() in plaats van recv()
        response = b""
        buffer = bytearray(1024)
        
        while True:
            try:
                bytes_read = sock.recv_into(buffer)
                if bytes_read == 0:
                    break
                response += buffer[:bytes_read]
            except OSError:
                break
        
        sock.close()
        
        response_text = response.decode("utf-8")
        print(f"Response: {response_text[:200]}...")
        
        if "\r\n\r\n" in response_text:
            headers, body = response_text.split("\r\n\r\n", 1)
            return json.loads(body)
        return None
            
    except Exception as e:
        print(f"Error: {e}")
        return None

# Boot test
for _ in range(2):
    all_on()
    time.sleep(0.1)
    all_off()
    time.sleep(0.1)

green.value = True
print("LED Controller started")

connect_wifi()

last_api_call = 0

while True:
    now = time.monotonic()
    
    if now - last_api_call >= SCAN_INTERVAL:
        last_api_call = now
        data = fetch_api()
        
        if data:
            current_level = data.get("level", 5)
            pattern = data.get("pattern", "GREEN")
            cve = data.get("cve_score", 0.0)
            info = data.get("info", "CLEAR")
            print(f">>> Level {current_level} | {pattern} | CVE:{cve} | {info}")
        else:
            print(">>> No API data")
            current_level = 4
    
    update_lights()
    time.sleep(0.02)