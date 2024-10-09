# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense
"""
Author: Mark Roberts (mdroberts1243) from Adafruit code
This test will initialize the display using displayio and draw a solid white
background, a smaller black rectangle, miscellaneous stuff and some white text.

"""

# Source https://learn.adafruit.com/adafruit-128x64-oled-featherwing/circuitpython


import board
import displayio
import digitalio
import json
import supervisor
import time

# can try this although it's byte-based and not text baed
# import usb_cdc

# Compatibility with both CircuitPython 8.x.x and 9.x.x.
# Remove after 8.x.x is no longer a supported release.
from i2cdisplaybus import I2CDisplayBus


"""
Can i remove this?

try:
    from i2cdisplaybus import I2CDisplayBus
except ImportError:
    from displayio import I2CDisplay as I2CDisplayBus
"""

import terminalio

# can try import bitmap_label below for alternative
from adafruit_display_text import label
import adafruit_displayio_sh1107

displayio.release_displays()
# oled_reset = board.D9

# Use for I2C
i2c = board.I2C()  # uses board.SCL and board.SDA
# i2c = board.STEMMA_I2C()  # For using the built-in STEMMA QT connector on a microcontroller
display_bus = I2CDisplayBus(i2c, device_address=0x3C)

# Buttons are noted in the pinout here https://learn.adafruit.com/adafruit-128x64-oled-featherwing/pinouts
# RP2040 is an Arm M0 Feather so 9,6,5 should be right

# Example code is from here https://learn.adafruit.com/adafruit-feather-rp2040-pico/digital-input
button_a = digitalio.DigitalInOut(board.D9)
button_a.switch_to_input(pull=digitalio.Pull.UP)

button_b = digitalio.DigitalInOut(board.D6)
button_b.switch_to_input(pull=digitalio.Pull.UP)

button_c = digitalio.DigitalInOut(board.D5)
button_c.switch_to_input(pull=digitalio.Pull.UP)

# SH1107 is vertically oriented 64x128
WIDTH = 128
HEIGHT = 64
BORDER = 2

display = adafruit_displayio_sh1107.SH1107(
    display_bus, width=WIDTH, height=HEIGHT, rotation=180
)
# Make the display context
splash = displayio.Group()
display.root_group = splash

color_bitmap = displayio.Bitmap(WIDTH, HEIGHT, 1)
color_palette = displayio.Palette(1)
color_palette[0] = 0xFFFFFF  # White

# white background
bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
splash.append(bg_sprite)

# Draw a smaller inner rectangle in black
inner_bitmap = displayio.Bitmap(WIDTH - BORDER * 2, HEIGHT - BORDER * 2, 1)
inner_palette = displayio.Palette(1)
inner_palette[0] = 0x000000  # Black
inner_sprite = displayio.TileGrid(
    inner_bitmap, pixel_shader=inner_palette, x=BORDER, y=BORDER
)
splash.append(inner_sprite)

"""
Example input for use in testing

{"GpuCoreTempC":26,"GpuHotSpotTempC":34.34375,"GpuPowerWatts":27.809999465942383,"CpuCoreTempC":50.50000762939453,"CpuCcdTempC":35.75,"CpuPackagePowerWatts":36.78437042236328}
{"GpuCoreTempC":26,"GpuHotSpotTempC":34.34375,"GpuPowerWatts":27.611000061035156,"CpuCoreTempC":48.87500762939453,"CpuCcdTempC":36.625,"CpuPackagePowerWatts":37.46200942993164}
"""

print("\nBuilding splash screen...")

cur_y_pos = 8
newline_offset = 9

title_label = label.Label(
    terminalio.FONT,
    text=f"GPU info",
    color=0xFFFFFF,
    x=8,
    y=cur_y_pos,
)
splash.append(title_label)
cur_y_pos += newline_offset
# add in new items
row_1 = label.Label(
    terminalio.FONT,
    text=f"",
    color=0xFFFFFF,
    x=8,
    y=cur_y_pos,
)
splash.append(row_1)
cur_y_pos += newline_offset

row_2 = label.Label(
    terminalio.FONT,
    text=f"",
    color=0xFFFFFF,
    x=8,
    y=cur_y_pos,
)
splash.append(row_2)
cur_y_pos += newline_offset

row_3 = label.Label(
    terminalio.FONT,
    text=f"",
    color=0xFFFFFF,
    x=8,
    y=cur_y_pos,
)
splash.append(row_3)
cur_y_pos += newline_offset

row_4 = label.Label(
    terminalio.FONT,
    text=f"",
    color=0xFFFFFF,
    x=8,
    y=cur_y_pos,
)
splash.append(row_4)

title_label.text = "Waiting..."

# Default to GPU info
page_to_display = "gpu"


print("Splash screen built, starting main loop")

dummy_value = 0.0

cpu_core_temp = dummy_value
cpu_ccd_temp = dummy_value
cpu_power_watts = dummy_value

gpu_core_temp_c = dummy_value
gpu_hot_spot_temp_c = dummy_value
gpu_power_watts = dummy_value
cpu_and_gpu_watts = dummy_value

while True:

    if supervisor.runtime.serial_bytes_available == 0:
        if not button_a.value:
            page_to_display = "gpu"
        if not button_b.value:
            page_to_display = "cpu"
        if not button_c.value:
            page_to_display = "other"
        # time.sleep(0.2)
    else:
        input_string = input().strip()

        # Blocking wait, this is what the code used to have
        # input_string = input().strip()
        if len(input_string) < 10:
            # useful for debugging
            print(f"got short string: {input_string}")
            continue

        json_data = json.loads(input_string)

        cpu_core_temp = json_data["CpuCoreTempC"]
        cpu_ccd_temp = json_data["CpuCcdTempC"]
        cpu_power_watts = json_data["CpuPackagePowerWatts"]

        gpu_core_temp_c = json_data["GpuCoreTempC"]
        gpu_hot_spot_temp_c = json_data["GpuHotSpotTempC"]
        gpu_power_watts = json_data["GpuPowerWatts"]

        cpu_and_gpu_watts = gpu_power_watts + cpu_power_watts

    if page_to_display == "gpu":
        title_label.text = "GPU Info"
        row_1.text = f"core: {gpu_core_temp_c:.1f} C"
        row_2.text = f"hot spot: {gpu_hot_spot_temp_c:.1f} C"
        row_3.text = f"power: {gpu_power_watts:.1f} W"
        row_4.text = f"+ cpu: {cpu_and_gpu_watts:.1f} W"

    elif page_to_display == "cpu":
        title_label.text = "CPU Info"
        row_1.text = f"core: {cpu_core_temp:.1f} C"
        row_2.text = f"ccd: {cpu_ccd_temp:.1f} C"
        row_3.text = f"power: {cpu_power_watts:.1f} W"
        row_4.text = f"+ gpu: {cpu_and_gpu_watts:.1f} W"

    else:
        title_label.text = page_to_display
        row_1.text = ""
        row_2.text = ""
        row_3.text = ""
        row_4.text = ""
