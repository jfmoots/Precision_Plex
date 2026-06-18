# Smart Current Sense Awning Control

Optional ESP32 + ACS758 current sensing can provide physical awning event detection.

Extension sequence:
- Extend
- Detect arm lock current threshold
- 100ms overrun
- 4000ms fabric tighten retract
- Stop and set position 100%

Retraction sequence:
- Retract
- Detect seated awning current threshold
- Stop and set position 0%

If telemetry is unavailable, the integration automatically falls back to traditional time-based operation.
