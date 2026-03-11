import board
from digitalio import DigitalInOut, Direction
import usb_cdc
from time import sleep, monotonic

# LED pins - GP0 to GP4
green = DigitalInOut(board.GP0)
blue = DigitalInOut(board.GP1)
yellow = DigitalInOut(board.GP2)
red = DigitalInOut(board.GP3)
white = DigitalInOut(board.GP4)  # Has buzzer attached

leds = [green, blue, yellow, red, white]

for led in leds:
    led.direction = Direction.OUTPUT
    led.value = False

current_level = 5
current_pattern = "GREEN"
last_update = 0
blink_state = False
police_state = 0  # For alternating police pattern

def all_off():
    for led in leds:
        led.value = False

def all_on():
    for led in leds:
        led.value = True

def parse_message(line):
    try:
        parts = line.strip().split(',')
        if len(parts) >= 2:
            level = int(parts[0])
            pattern = parts[1].strip().upper()
            info = parts[2].strip() if len(parts) > 2 else ""
            return level, pattern, info
    except:
        pass
    return None, None, None

def update_lights():
    global last_update, blink_state, police_state
    
    now = monotonic()
    
    # LEVEL 5 - Safe: Green solid
    if current_level == 5:
        all_off()
        green.value = True
    
    # LEVEL 4 - Low threat: Blue slow blink
    elif current_level == 4:
        if now - last_update > 0.6:
            blink_state = not blink_state
            last_update = now
        all_off()
        blue.value = blink_state
    
    # LEVEL 3 - Medium threat: Yellow faster blink
    elif current_level == 3:
        if now - last_update > 0.3:
            blink_state = not blink_state
            last_update = now
        all_off()
        yellow.value = blink_state
    
    # LEVEL 2 - High threat: Red rapid blink
    elif current_level == 2:
        if now - last_update > 0.15:
            blink_state = not blink_state
            last_update = now
        all_off()
        red.value = blink_state
    
    # LEVEL 1 - CRITICAL: Police lights (Red/White alternate) + buzzer on white
    elif current_level == 1:
        if now - last_update > 0.1:  # Very fast
            last_update = now
            police_state = (police_state + 1) % 4  # 4-step cycle
        
        all_off()
        
        # Police pattern: Red-Red-White-White alternating
        if police_state == 0 or police_state == 1:
            red.value = True
        else:
            white.value = True  # Buzzer sounds here

# Boot test - flash all 2 times
for _ in range(2):
    all_on()
    sleep(0.1)
    all_off()
    sleep(0.1)

green.value = True  # Start green

print("Security Monitor Started")

while True:
    # Check serial
    if usb_cdc.console.in_waiting > 0:
        try:
            line = usb_cdc.console.readline().decode('utf-8').strip()
            if line:
                level, pattern, info = parse_message(line)
                if level is not None and 1 <= level <= 5:
                    if level != current_level:
                        current_level = level
                        current_pattern = pattern
                        print(f"Level {level}: {pattern}")
        except Exception as e:
            print(f"Error: {e}")
    
    # Update lights
    update_lights()
    
    sleep(0.02)  # 50Hz refresh