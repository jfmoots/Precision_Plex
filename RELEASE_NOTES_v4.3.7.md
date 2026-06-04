# Precision Plex v4.3.7 - Generator Runtime Field Diagnostics

This diagnostic build keeps the v4.3.5/v4.3.6 generator runtime protections and adds more focused tracing around the suspected runtime field-width issue.

## What changed

- Adds byte-level diagnostics for generator runtime packets.
- Logs bytes 6-9 and multiple candidate interpretations.
- Adds masked 12-bit and 14-bit candidates for the suspected runtime field.
- Adds a candidate that combines the previously accepted high byte with the current low byte.
- Emits warning-level diagnostics only for rejected or non-standard runtime frames; normal accepted `0x0004` frames are debug-level.

## Purpose

This is intended to prove whether packets such as `0x0060` are non-runtime/status frames being misread as runtime, or whether the generator runtime field uses a narrower byte/nibble layout than originally assumed.
