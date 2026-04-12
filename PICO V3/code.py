# code.py - Dual buzzer version with Mario themes (FIXED)
import board
from digitalio import DigitalInOut, Direction, Pull
import pwmio
import wifi
import socketpool
import time
import json
import random

WIFI_SSID = "881ifjAjnd"
WIFI_PASSWORD = "12345678"
API_HOST = "10.118.212.127"
API_PORT = 5000
SCAN_INTERVAL = 5

# LED pins
green = DigitalInOut(board.GP0)
blue = DigitalInOut(board.GP1)
yellow = DigitalInOut(board.GP2)
red = DigitalInOut(board.GP3)
white = DigitalInOut(board.GP4)

# DUAL BUZZERS - GP16 and GP18
buzzer_a = pwmio.PWMOut(board.GP16, duty_cycle=0, frequency=440, variable_frequency=True)
buzzer_b = pwmio.PWMOut(board.GP18, duty_cycle=0, frequency=440, variable_frequency=True)

# Track which buzzer is active
active_buzzer = 0  # 0 = buzzer_a, 1 = buzzer_b

# MUTE BUTTON on GP17
mute_button = DigitalInOut(board.GP17)
mute_button.direction = Direction.INPUT
mute_button.pull = Pull.UP

leds = [green, blue, yellow, red, white]

for led in leds:
    led.direction = Direction.OUTPUT
    led.value = False

current_level = 5
previous_level = 5
last_update = 0
blink_state = False
police_state = 0

buzzer_playing = False
buzzer_muted = False
last_button_state = True
button_debounce_time = 0
mute_button_pressed = False

current_song = 0
note_index = 0
last_note_time = 0

# ========== ALL NOTE DEFINITIONS (FIXED - added missing notes) ==========
NOTE_A3 = 220
NOTE_AS3 = 233
NOTE_B3 = 247
NOTE_C4 = 262
NOTE_CS4 = 277
NOTE_D4 = 294
NOTE_DS4 = 311
NOTE_E4 = 330
NOTE_FS4 = 370
NOTE_G4 = 392
NOTE_GS4 = 415
NOTE_A4 = 440
NOTE_AS4 = 466
NOTE_B4 = 494
NOTE_C5 = 523
NOTE_CS5 = 554
NOTE_D5 = 587
NOTE_DS5 = 622
NOTE_E5 = 659
NOTE_F5 = 698
NOTE_FS5 = 740
NOTE_G5 = 784
NOTE_GS5 = 831
NOTE_A5 = 880
NOTE_AS5 = 932
NOTE_B5 = 988
NOTE_C6 = 1047
NOTE_CS6 = 1109
NOTE_D6 = 1175
NOTE_DS6 = 1245
NOTE_E6 = 1319
NOTE_F6 = 1397

# 1. Super Mario Bros Main Theme
SONG_MARIO_MAIN = [
    (NOTE_E5, 200), (NOTE_E5, 200), (0, 200), (NOTE_E5, 200), (0, 200),
    (NOTE_C5, 200), (NOTE_E5, 200), (0, 200), (NOTE_G5, 400), (0, 400),
    (NOTE_G4, 400), (0, 400),
    (NOTE_C5, 300), (NOTE_G4, 300), (NOTE_E4, 300),
    (NOTE_A4, 300), (NOTE_B4, 300), (NOTE_AS4, 200), (NOTE_A4, 300),
    (NOTE_G4, 200), (NOTE_E5, 200), (NOTE_G5, 200), (NOTE_A5, 300),
    (NOTE_F5, 200), (NOTE_G5, 200), (0, 200), (NOTE_E5, 300), (0, 200),
    (NOTE_C5, 200), (NOTE_D5, 200), (NOTE_B4, 400), (0, 400),
]

# 2. Mario Underground Theme
SONG_MARIO_UNDERGROUND = [
    (NOTE_C4, 200), (NOTE_CS4, 200), (NOTE_D4, 200), (NOTE_DS4, 200),
    (NOTE_E4, 400), (NOTE_DS4, 200), (NOTE_D4, 200), (NOTE_CS4, 200),
    (NOTE_C4, 400), (0, 200),
    (NOTE_A3, 200), (NOTE_AS3, 200), (NOTE_B3, 200), (NOTE_C4, 400),
    (0, 400),
    (NOTE_C4, 200), (NOTE_CS4, 200), (NOTE_D4, 200), (NOTE_DS4, 200),
    (NOTE_E4, 400), (NOTE_DS4, 200), (NOTE_D4, 200), (NOTE_CS4, 200),
    (NOTE_C4, 600), (0, 600),
]

# 3. Mario Warning/Hurry Up Theme
SONG_MARIO_WARNING = [
    (NOTE_B5, 150), (0, 50), (NOTE_B5, 150), (0, 50),
    (NOTE_B5, 150), (0, 50), (NOTE_B5, 150), (0, 200),
    (NOTE_A5, 150), (0, 50), (NOTE_A5, 150), (0, 50),
    (NOTE_A5, 150), (0, 50), (NOTE_A5, 150), (0, 200),
    (NOTE_G5, 150), (0, 50), (NOTE_G5, 150), (0, 50),
    (NOTE_G5, 150), (0, 50), (NOTE_G5, 150), (0, 200),
    (NOTE_FS5, 300), (NOTE_G5, 300), (NOTE_A5, 600),
    (0, 400),
]

SONGS = [SONG_MARIO_MAIN, SONG_MARIO_UNDERGROUND, SONG_MARIO_WARNING]
SONG_NAMES = ["MARIO_MAIN", "MARIO_UNDERGROUND", "MARIO_WARNING"]

def all_off():
    for led in leds:
        led.value = False
    buzzer_a.duty_cycle = 0
    buzzer_b.duty_cycle = 0

def all_on():
    for led in leds:
        led.value = True

def play_tone(frequency, duration_ms):
    """Play tone on active buzzer with clean switching"""
    global active_buzzer
    
    if buzzer_muted or frequency == 0:
        buzzer_a.duty_cycle = 0
        buzzer_b.duty_cycle = 0
        time.sleep(duration_ms / 1000)
        return
    
    # Dual buzzer technique: prepare next note on inactive buzzer
    if active_buzzer == 0:
        buzzer_b.frequency = int(frequency)
        buzzer_b.duty_cycle = 32768
        time.sleep(0.001)
        buzzer_a.duty_cycle = 0
        active_buzzer = 1
    else:
        buzzer_a.frequency = int(frequency)
        buzzer_a.duty_cycle = 32768
        time.sleep(0.001)
        buzzer_b.duty_cycle = 0
        active_buzzer = 0
    
    time.sleep(duration_ms / 1000)
    
    if active_buzzer == 0:
        buzzer_a.duty_cycle = 0
    else:
        buzzer_b.duty_cycle = 0

def check_mute_button():
    global buzzer_muted, last_button_state, button_debounce_time, mute_button_pressed
    
    now = time.monotonic()
    current_state = mute_button.value
    
    if current_state != last_button_state:
        button_debounce_time = now
        last_button_state = current_state
    
    if (now - button_debounce_time) > 0.05:
        if last_button_state == False and not mute_button_pressed:
            mute_button_pressed = True
            buzzer_muted = not buzzer_muted
            if buzzer_muted:
                buzzer_a.duty_cycle = 0
                buzzer_b.duty_cycle = 0
                print("🔇 MARIO MUTED")
            else:
                print("🔊 MARIO UNMUTED")
            return True
        elif last_button_state == True:
            mute_button_pressed = False
    
    return False

def update_buzzer():
    global buzzer_playing, current_song, note_index, last_note_time, active_buzzer
    
    if current_level > 4:
        if buzzer_playing:
            buzzer_a.duty_cycle = 0
            buzzer_b.duty_cycle = 0
            buzzer_playing = False
        return
    
    if buzzer_muted:
        return
    
    now = time.monotonic()
    
    if not buzzer_playing:
        buzzer_playing = True
        current_song = random.randint(0, 2)
        note_index = 0
        last_note_time = now
        active_buzzer = 0
        print(f"🍄 MARIO THEME: {SONG_NAMES[current_song]} (Level {current_level})")
    
    song = SONGS[current_song]
    if note_index < len(song):
        freq, duration = song[note_index]
        play_tone(freq, duration)
        note_index += 1
        
        if note_index >= len(song):
            note_index = 0
            time.sleep(0.2)
    else:
        note_index = 0

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
        
        post_data = json.dumps({"device": "pico_w"})
        
        request = (
            f"POST /api/security/status HTTP/1.1\r\n"
            f"Host: {API_HOST}\r\n"
            f"Content-Type: application/json\r\n"
            f"Content-Length: {len(post_data)}\r\n"
            f"Connection: close\r\n"
            f"\r\n"
            f"{post_data}"
        )
        
        sock.send(request.encode())
        
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

# Test both buzzers with Mario coin sound
print("Testing dual buzzers...")
play_tone(NOTE_B5, 100)
time.sleep(0.1)
play_tone(NOTE_E6, 400)

green.value = True
print("Mario Security System initialized")
print("Dual buzzers on GP16 and GP18 - no clicking noise!")
print("Alarm for levels 1-4, silent for level 5")
print("GP0=Green, GP1=Blue, GP2=Yellow, GP3=Red, GP4=White")
print("Buzzer A=GP16, Buzzer B=GP18, Button=GP17")

connect_wifi()

last_api_call = 0

while True:
    now = time.monotonic()
    
    check_mute_button()
    
    if now - last_api_call >= SCAN_INTERVAL:
        last_api_call = now
        data = fetch_api()
        
        if data:
            new_level = data.get("level", 5)
            previous_level = current_level
            current_level = new_level
            
            if previous_level <= 4 and current_level > 4 and buzzer_muted:
                buzzer_muted = False
                print("🔊 Auto-unmuted (threat cleared)")
            
            pattern = data.get("pattern", "GREEN")
            cve = data.get("cve_score", 0.0)
            info = data.get("info", "CLEAR")
            mute_status = "[MUTED]" if buzzer_muted else ""
            print(f">>> Level {current_level} | {pattern} | CVE:{cve} | {info} {mute_status}")
            
            if current_level > 4 and buzzer_playing:
                buzzer_a.duty_cycle = 0
                buzzer_b.duty_cycle = 0
                buzzer_playing = False
        else:
            print(">>> No API data")
            previous_level = current_level
            current_level = 4
    
    update_lights()
    
    if current_level <= 4:
        update_buzzer()
    
    time.sleep(0.01)