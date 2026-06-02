# State and Level Mapping

## 02BB State Notifications

State notifications are received through the `02BB` payload stream.

The payload is decoded as multiple big-endian 16-bit words.

### Word 0

| Bit | Function | Status | Notes |
|---:|---|---|---|
| `0x0002` | Awning In Active | Verified | Awning retracting |
| `0x0004` | Awning Out Active | Verified | Awning extending |
| `0x0080` | Sofa Slide In Active | Verified | Sofa slide retracting |
| `0x0100` | Awning Light | Verified | Light on/off state |
| `0x1000` | Water Heater | Verified | Heater on/off state |
| `0x8000` | Water Pump | Verified | Pump on/off state |

### Word 1

| Bit | Function | Status | Notes |
|---:|---|---|---|
| `0x0100` | Sofa Slide Out Active | Verified | Sofa slide extending |
| `0x0200` | Wardrobe Slide In Active | Verified | Wardrobe slide retracting |
| `0x0400` | Wardrobe Slide Out Active | Verified | Wardrobe slide extending |
| `0x0800` | Bed Slide In Active | Verified | Bed slide retracting |
| `0x1000` | Bed Slide Out Active | Verified | Bed slide extending |

## 02AA Level Monitor Notifications

The Level Monitor page is decoded from `02AA`, observed at handle `0x002B`.

Example:

```text
00 83 06 3F 3F 50 ...
```

| Field | Source | Mapping |
|---|---|---|
| Coach Battery | bytes 0-1, big-endian tenths of volts | `0x0083` = 13.1 V |
| Fresh Water | byte 2 low nibble | `0=0%`, `3=33%`, `6=67%`, `A=100%` |
| Grey Water | byte 3 high nibble | `0=0%`, `3=33%`, `6=67%`, `A=100%` |
| Black Water | byte 4 high nibble | `0=0%`, `3=33%`, `6=67%`, `A=100%` |
| LP Gas | byte 5 high nibble | `0=0%`, `2=25%`, `5=50%`, `7=75%`, `A=100%` |

## Contribution Notes

When identifying a new state bit or level field:

1. Capture a baseline idle state.
2. Change one physical function or level at a time.
3. Compare only the relevant notification stream.
4. Confirm the value returns when the physical state returns.
5. Document coach model, year, and function name.
