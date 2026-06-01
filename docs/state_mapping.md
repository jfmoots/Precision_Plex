# State Mapping

State notifications are received through the `02BB` payload stream.

The payload is decoded as multiple big-endian 16-bit words.

## Word 0

| Bit | Function | Status | Notes |
|---:|---|---|---|
| `0x0002` | Awning In Active | Verified | Awning retracting |
| `0x0004` | Awning Out Active | Verified | Awning extending |
| `0x0100` | Awning Light | Verified | Light on/off state |
| `0x1000` | Water Heater | Verified | Heater on/off state |
| `0x8000` | Water Pump | Verified | Pump on/off state |

## Word 1

| Bit | Function | Status | Notes |
|---:|---|---|---|
| `0x0200` | Wardrobe Slide In Active | Verified | Wardrobe slide retracting |
| `0x0400` | Wardrobe Slide Out Active | Verified | Wardrobe slide extending |
| `0x0800` | Bed Slide In Active | Verified | Bed slide retracting |
| `0x1000` | Bed Slide Out Active | Verified | Bed slide extending |

## Unknown / Future Bits

Potential future functions:

- Sofa Slide
- Wardrobe Slide
- Additional lighting circuits
- Generator functions
- Tank monitoring
- HVAC-related functions
- Coach-specific accessories

## Contribution Notes

When identifying a new state bit:

1. Subscribe to `02BB` notifications.
2. Capture baseline idle state.
3. Activate one function at a time.
4. Compare changed 16-bit words.
5. Confirm the bit clears when the function stops.
6. Document coach model, year, and function name.


## Sofa Slide State Bits

Captured from Sofa slide packet traces.

| Notification | Word Index | Bit | Function | Status |
|---|---:|---:|---|---|
| `0x002F` | 1 | `0x0100` | Sofa Slide Out Active | Verified in trace |
| `0x002F` | 0 | `0x0080` | Sofa Slide In Active | Verified in trace |



## Reference Calibrations

These travel times were validated on a Precision Plex system installed in a **2022 Forest River Georgetown GT5 34M5 Motorhome**.

| Device | Open / Out | Close / In |
|---|---:|---:|
| Awning | 18 seconds | 25 seconds |
| Bed Slide | 28 seconds | 24 seconds |
| Wardrobe Slide | 18 seconds | 17 seconds |
| Sofa Slide | 32 seconds | 28 seconds |

Travel times vary by coach, slide mechanism, battery voltage, maintenance condition, and motor wear. These values are reference calibrations for this specific Georgetown GT5 34M5 installation and can be adjusted through the Home Assistant Number entities without modifying the integration.
