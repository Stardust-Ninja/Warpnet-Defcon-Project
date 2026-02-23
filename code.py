import board
from digitalio import DigitalInOut, Direction
from time import sleep

# Define LEDs
leds = [
    DigitalInOut(board.GP0),  # Green
    DigitalInOut(board.GP1),  # Dark Blue
    DigitalInOut(board.GP2),  # Yellow
    DigitalInOut(board.GP3),  # Red
    DigitalInOut(board.GP4),  # See-through (white)
]

# Set all LEDs as outputs
for led in leds:
    led.direction = Direction.OUTPUT

# Function to set threat level (1-5)
def set_level(level):
    for i, led in enumerate(leds):
        led.value = True if i < level else False

# Function to blink the top LED (level 5)
def blink_top(times=5, speed=0.2):
    top_led = leds[4]
    for _ in range(times):
        top_led.value = True
        sleep(speed)
        top_led.value = False
        sleep(speed)

# Main loop: go through levels
while True:
    for lvl in range(1, 6):  # Levels 1 → 5
        set_level(lvl)
        sleep(1)
        if lvl == 5:
            blink_top(times=5)