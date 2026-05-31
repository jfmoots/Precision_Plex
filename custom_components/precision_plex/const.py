"""Constants for Precision Plex read-only monitor."""

from homeassistant.const import CONF_ADDRESS

DOMAIN = "precision_plex"
PLATFORMS = ["binary_sensor", "light", "switch", "cover", "number"]

DEFAULT_TARGET_ADDRESS = "80:4B:50:D2:44:B4"
TARGET_SERVICE_UUID = "00726f62-6f74-7061-6a61-6d61732e6361"

PAIRING_CHARACTERISTIC_UUID = "01556963-6172-6173-6f6c-7574696f6e73"
PAIRING_INIT_PAYLOAD = bytes.fromhex("06")

STATE_CHARACTERISTIC_UUID = "02bb6f62-6f74-7061-6a61-6d61732e6361"

STATE_BITS = {
    "awning_light": {
        "name": "Awning Light State",
        "word_index": 0,
        "bit": 0x0100,
        "device_class": "light",
    },
    "awning_in": {
        "name": "Awning In Active",
        "word_index": 0,
        "bit": 0x0002,
        "device_class": "moving",
    },
    "awning_out": {
        "name": "Awning Out Active",
        "word_index": 0,
        "bit": 0x0004,
        "device_class": "moving",
    },
    "water_heater": {
        "name": "Water Heater State",
        "word_index": 0,
        "bit": 0x1000,
        "device_class": "power",
    },
    "water_pump": {
        "name": "Water Pump State",
        "word_index": 0,
        "bit": 0x8000,
        "device_class": "power",
    },
    "bed_slide_out": {
        "name": "Bed Slide Out",
        "word_index": 1,
        "bit": 0x1000,
        "device_class": "moving",
    },
    "bed_slide_in": {
        "name": "Bed Slide In",
        "word_index": 1,
        "bit": 0x0800,
        "device_class": "moving",
    },
}


CONTROL_CHARACTERISTIC_UUID = "03726f62-6f74-7061-6a61-6d61732e6361"

AWNING_LIGHT_ON = bytes.fromhex(
    "55 1D 10 0B 00 3F 00 00 00 00 00 00 00 00 00 34"
)

AWNING_LIGHT_OFF = bytes.fromhex(
    "55 1D 10 0B 00 00 00 00 00 00 00 00 00 00 00 73"
)

COMMAND_PAYLOADS = {
    "awning_light_on": AWNING_LIGHT_ON,
    "awning_light_off": AWNING_LIGHT_OFF,
}


# The Precision app writes these as a momentary button action:
#   release/neutral frame, then press frame.
# The press frame toggles the awning light rather than setting an absolute state.
AWNING_LIGHT_RELEASE = AWNING_LIGHT_OFF
AWNING_LIGHT_PRESS = AWNING_LIGHT_ON

AWNING_LIGHT_TAP_SEQUENCE = [
    AWNING_LIGHT_RELEASE,
    AWNING_LIGHT_PRESS,
]

WATER_PUMP_TAP = bytes.fromhex(
    "55 1D 10 0B 00 07 00 00 00 00 00 00 00 00 00 6C"
)

WATER_HEATER_TAP = bytes.fromhex(
    "55 1D 10 0B 00 04 00 00 00 00 00 00 00 00 00 6F"
)

AWNING_OUT_RELEASE = bytes.fromhex(
    "55 1D 10 0B 00 0A 00 00 00 00 00 00 00 00 00 69"
)
AWNING_OUT_HOLD = bytes.fromhex(
    "55 1D 10 0B 00 0A 00 01 00 00 00 00 00 00 00 68"
)
AWNING_IN_RELEASE = bytes.fromhex(
    "55 1D 10 0B 00 09 00 00 00 00 00 00 00 00 00 6A"
)
AWNING_IN_HOLD = bytes.fromhex(
    "55 1D 10 0B 00 09 00 01 00 00 00 00 00 00 00 69"
)

# Bed slide command packets captured from the Precision iOS app.
BED_SLIDE_OUT_RELEASE = bytes.fromhex(
    "55 1D 10 0B 00 14 00 00 00 00 00 00 00 00 00 5F"
)
BED_SLIDE_OUT_HOLD = bytes.fromhex(
    "55 1D 10 0B 00 14 00 01 00 00 00 00 00 00 00 5E"
)
BED_SLIDE_IN_RELEASE = bytes.fromhex(
    "55 1D 10 0B 00 13 00 00 00 00 00 00 00 00 00 60"
)
BED_SLIDE_IN_HOLD = bytes.fromhex(
    "55 1D 10 0B 00 13 00 01 00 00 00 00 00 00 00 5F"
)
