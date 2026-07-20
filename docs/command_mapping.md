# Command Mapping

All known commands are written to the control characteristic:

```text
03726f62-6f74-7061-6a61-6d61732e6361
```

## Momentary / Toggle Commands

### Awning Light Toggle

```text
55 1D 10 0B 00 3F 00 00 00 00 00 00 00 00 00 34
```

Status: Verified

### Water Pump Toggle

```text
55 1D 10 0B 00 07 00 00 00 00 00 00 00 00 00 6C
```

Status: Verified

### Water Heater Toggle

```text
55 1D 10 0B 00 04 00 00 00 00 00 00 00 00 00 6F
```

Status: Verified

## Awning Commands

### Awning Out / Extend Release

```text
55 1D 10 0B 00 0A 00 00 00 00 00 00 00 00 00 69
```

Status: Verified

### Awning Out / Extend Hold

```text
55 1D 10 0B 00 0A 00 01 00 00 00 00 00 00 00 68
```

Status: Verified

### Awning In / Retract Release

```text
55 1D 10 0B 00 09 00 00 00 00 00 00 00 00 00 6A
```

Status: Verified

### Awning In / Retract Hold

```text
55 1D 10 0B 00 09 00 01 00 00 00 00 00 00 00 69
```

Status: Verified

## Bed Slide Commands

### Bed Slide Out / Extend Release

```text
55 1D 10 0B 00 14 00 00 00 00 00 00 00 00 00 5F
```

Status: Verified

### Bed Slide Out / Extend Hold

```text
55 1D 10 0B 00 14 00 01 00 00 00 00 00 00 00 5E
```

Status: Verified

### Bed Slide In / Retract Release

```text
55 1D 10 0B 00 13 00 00 00 00 00 00 00 00 00 60
```

Status: Verified

### Bed Slide In / Retract Hold

```text
55 1D 10 0B 00 13 00 01 00 00 00 00 00 00 00 5F
```

Status: Verified


## Wardrobe Slide Commands

### Wardrobe Slide Out / Extend Release

```text
55 1D 10 0B 00 12 00 00 00 00 00 00 00 00 00 61
```

Status: Verified

### Wardrobe Slide Out / Extend Hold

```text
55 1D 10 0B 00 12 00 01 00 00 00 00 00 00 00 60
```

Status: Verified

### Wardrobe Slide In / Retract Release

```text
55 1D 10 0B 00 11 00 00 00 00 00 00 00 00 00 62
```

Status: Verified

### Wardrobe Slide In / Retract Hold

```text
55 1D 10 0B 00 11 00 01 00 00 00 00 00 00 00 61
```

Status: Verified

## Movement Command Behavior

Movement commands behave like press-and-hold controls.

The mobile app pattern is:

1. Send release/neutral.
2. Send hold repeatedly, approximately every 300 ms.
3. Send release/neutral when the button is released.

The integration reproduces this pattern for cover entities.

On the tested coach, the authoritative PID32 output bitmap is scheduled about
once every five seconds. Home Assistant commands therefore publish a
provisional requested state immediately. The next matching PID32 or BLE 02BB
value confirms that request without a visible state reversal. If confirmation
does not arrive within 12 seconds, the integration returns to authoritative
telemetry.

Captured LIN command behavior uses the lower movement opcode for the initial
press/release phase and the same opcode plus `0x40` while actively held. The
touchscreen channel returns to `3F 00` after release.


## Sofa Slide Commands

### Sofa Slide Out / Extend Release

```text
55 1D 10 0B 00 10 00 00 00 00 00 00 00 00 00 63
```

Status: Verified

### Sofa Slide Out / Extend Hold

```text
55 1D 10 0B 00 10 00 01 00 00 00 00 00 00 00 62
```

Status: Verified

### Sofa Slide In / Retract Release

```text
55 1D 10 0B 00 0F 00 00 00 00 00 00 00 00 00 64
```

Status: Verified

### Sofa Slide In / Retract Hold

```text
55 1D 10 0B 00 0F 00 01 00 00 00 00 00 00 00 63
```

Status: Verified

### Stop / Release

```text
55 1D 10 0B 00 3F 00 00 00 00 00 00 00 00 00 34
```

Status: Verified shared movement stop command



## Generator Commands

Generator commands are written to handle `0x0037` in the captured mobile app traces.

### Generator Start Press

```text
55 1D 10 0B 00 3E 02 00 00 00 00 00 00 00 00 33
```

Status: Verified

### Generator Stop Press

```text
55 1D 10 0B 00 3E 03 00 00 00 00 00 00 00 00 32
```

Status: Verified

### Generator Release / Neutral

```text
55 1D 10 0B 00 3F 00 00 00 00 00 00 00 00 00 34
```

Status: Verified

### Generator Safety Interlocks

Home Assistant only allows Generator Start when live generator telemetry says the generator is not running.

Home Assistant only allows Generator Stop when live generator telemetry says the generator is running.

Both commands are blocked when generator telemetry is unknown or unavailable.


### Generator AutoStart Press

```text
55 1D 10 0B 00 3E 0A 00 00 00 00 00 00 00 00 2B
```

Status: Verified

### Generator AutoStop Press

```text
55 1D 10 0B 00 3E 0B 00 00 00 00 00 00 00 00 2A
```

Status: Verified

### Generator AutoStart / AutoStop Notes

AutoStart and AutoStop are managed generator sequences, not persistent toggle modes. The Precision Plex controller primes and attempts the generator start/stop process. During failed AutoStart testing, the controller attempted four starts and then published the `Will Not Start` status.

Safety interlocks match the normal Start/Stop controls:

- AutoStart is only available when generator telemetry indicates the generator is not running.
- AutoStop is only available when generator telemetry indicates the generator is running.
- Both are blocked when generator telemetry is unknown or unavailable.
