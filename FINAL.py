from machine import Pin, SPI, ADC
import max7219
import time
import random
import neopixel
import math

# HOW IT WILL DISPLAY
spi = SPI(1, baudrate=80000, polarity=0, phase=0,
          sck=Pin(18), mosi=Pin(23))

cs1 = Pin(5, Pin.OUT)
cs2 = Pin(15, Pin.OUT)

display1 = max7219.Matrix8x8(spi, cs1, 4)
display2 = max7219.Matrix8x8(spi, cs2, 4)

WIDTH = 32
HEIGHT = 8

# MIC SETTINGS
mic = ADC(Pin(34))
mic.atten(ADC.ATTN_11DB)

baseline = 1900
prev_value = 0

# JOYSTICK SETTINGS
joy = ADC(Pin(35))
joy.atten(ADC.ATTN_11DB)

mode = 2
prev_region = 2

# NEOPIXEL STRIP 
NUM_LEDS = 10
np = neopixel.NeoPixel(Pin(4), NUM_LEDS)

breath_phase = 0

# ARRAYS
current = [0]*WIDTH
target = [0]*WIDTH

NOISE_THRESHOLD = 20

# FILTERS
low = 0
high = 0

# MODES (FOR COLOUR AND SOUND TYPE)
def get_color(mode, brightness):

    if mode == 1:
        # PINK-BASS
        return (int(150 * brightness), 0, int(50 * brightness))

    elif mode == 2:
        # RED- FULL
        return (int(150 * brightness), 0, 0)

    else:
        # YELLOW- TREBLE
        return (int(150 * brightness), int(50 * brightness), 0)

# NEOPIXEL BREATHING SETTINGS 
def update_neopixel(mode, phase):

    

    # breathing wave (0 - 1 - 0)
    brightness = (math.sin(phase) + 1) / 2

    color = get_color(mode, brightness)

    for i in range(NUM_LEDS):
        np[i] = color

    np.write()

# MAIN LOOP
while True:

    display1.fill(0)
    display2.fill(0)

    # JOYSTICK FUNCTIONS
    joy_val = joy.read()

    if joy_val < 1200:
        region = 1
    elif joy_val > 2800:
        region = 3
    else:
        region = 2

    if region != prev_region:

        if prev_region == 2 and region == 1:
            mode += 1
        elif prev_region == 2 and region == 3:
            mode -= 1

        if mode < 1:
            mode = 1
        if mode > 3:
            mode = 3

        if mode == 1:
            print("🎛 MODE: PINK (BASS)")
        elif mode == 2:
            print("🎛 MODE: RED (FULL)")
        else:
            print("🎛 MODE: YELLOW (TREBLE)")

    prev_region = region

    # NEOPIXEL BREATHING EFFECT
    breath_phase += 0.35
    update_neopixel(mode, breath_phase)

    # MIC
    value = mic.read()
    baseline = (baseline * 0.9) + (value * 0.1)

    amplitude = abs(value - baseline)
    delta = abs(value - prev_value)
    prev_value = value

    if amplitude < NOISE_THRESHOLD:
        amplitude = 0
        delta = 0

    low = (low * 0.95) + (amplitude * 0.05)
    full = (amplitude * 0.6) + (low * 0.4)
    high = (high * 0.3) + (delta * 0.7)

    if mode == 1:
        band_val = low
    elif mode == 2:
        band_val = full
    else:
        band_val = high

    # THE VISUALIZER
    for x in range(WIDTH):

        if amplitude == 0:
            target[x] = 0
        else:
            if mode == 2:
                variation = band_val + random.randint(-25, 25)
            else:
                variation = band_val + random.randint(-15, 15)

            height = int(variation / 10)

            if height < 0:
                height = 0
            if height > HEIGHT:
                height = HEIGHT

            target[x] = height

        if current[x] < target[x]:
            current[x] += 1
        elif current[x] > target[x]:
            current[x] -= 1

        if amplitude == 0:
            current[x] = max(0, current[x] - 1)

        h = current[x]

        for y in range(h):
            display1.pixel(x, 7 - y, 1)

        for y in range(h):
            display2.pixel(x, y, 1)

    display1.show()
    display2.show()

    time.sleep(0.05)