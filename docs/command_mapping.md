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

## Movement Command Behavior

Movement commands behave like press-and-hold controls.

The mobile app pattern is:

1. Send release/neutral.
2. Send hold repeatedly, approximately every 300 ms.
3. Send release/neutral when the button is released.

The integration reproduces this pattern for cover entities.
