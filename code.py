import board
from digitalio import DigitalInOut, Direction
import usb_cdc
from time import sleep

# Pas deze pins aan naar jouw bedrading
green = DigitalInOut(board.GP0)
blue = DigitalInOut(board.GP1)
yellow = DigitalInOut(board.GP2)
red = DigitalInOut(board.GP3)
white = DigitalInOut(board.GP4)

leds = [green, blue, yellow, red, white]

for led in leds:
    led.direction = Direction.OUTPUT
    led.value = False

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
        # Kritiek: alles knippert
        for _ in range(3):
            for led in leds:
                led.value = True
            sleep(0.2)
            for led in leds:
                led.value = False
            sleep(0.2)

while True:
    if usb_cdc.console.in_waiting > 0:
        line = usb_cdc.console.readline().decode().strip()
        if line.isdigit():
            set_defcon(int(line))
