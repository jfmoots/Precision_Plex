# Precision Plex v5.5.6 — Fast PID1F/PID5E Command Intent

This release replaces transport-specific UI patches with one normalized LIN
command-intent path. Pair it with ESPHome Precision Plex LIN firmware v0.6.3.

## Faster state response from every controller

- Observes valid PID1F touchscreen and PID5E Wireless TP intent events.
- Updates awning light, water heater, tank heater, water pump, patio awning,
  and all three slide movement states as soon as the command appears on LIN.
- Applies the same behavior to commands originating in Home Assistant, the
  factory touchscreen, or another Wireless TP client.

## One normalized state model

- Treats the lower motion request opcode and its `+0x40` active form as one
  logical motion start.
- Ignores repeated hold frames and PID5E housekeeping traffic.
- Treats `3F 00` as a stop only for the active motion on that same channel.
- Processes each bridge command sequence once, including an injected PID5E
  command followed by its bus echo.

## Authoritative confirmation and compatibility

- Keeps PID32/02BB as authoritative state confirmation.
- Expires unconfirmed requested state safely after 12 seconds.
- Uses the older local Home Assistant provisional-state behavior only when the
  installed bridge does not advertise command-intent support.
- Retains independent source freshness grace periods; those solve rotating LIN
  availability and are separate from command responsiveness.
