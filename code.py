import board
from digitalio import DigitalInOut, Direction
import usb_cdc
from time import sleep

# Pas de pins aan naar jouw LED bedrading
green = DigitalInOut(board.GP0)
blue = DigitalInOut(board.GP1)
yellow = DigitalInOut(board.GP2)
red = DigitalInOut(board.GP3)
white = DigitalInOut(board.GP4)

leds = [green, blue, yellow, red, white]

for led in leds:
    led.direction = Direction.OUTPUT
    led.value = False

current_level = None  # Houdt bij welk level momenteel actief is

def all_off():
    for led in leds:
        led.value = False

def set_defcon(level):
    all_off()
    
    if level == 5:
        green.value = True
    elif level == 4:
        blue.value = True
    elif level == 3:
        yellow.value = True
    elif level == 2:
        red.value = True
    elif level == 1:
        # DEFCON 1: alles continu knipperen
        pass  # knipperlogica komt in de main loop

while True:
    # Check voor nieuw level via USB
    if usb_cdc.console.in_waiting > 0:
        line = usb_cdc.console.readline().decode().strip()
        if line.isdigit():
            new_level = int(line)
            if new_level != current_level:
                current_level = new_level
                set_defcon(current_level)

    # Knipperlogica voor DEFCON 1
    if current_level == 1:
        for led in leds:
            led.value = not led.value
        sleep(0.3)
    else:
        sleep(0.1)
