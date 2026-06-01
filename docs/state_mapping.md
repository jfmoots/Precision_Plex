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
