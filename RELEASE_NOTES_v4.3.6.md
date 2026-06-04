# Precision Plex v4.3.6

Generator runtime diagnostic build.

This release keeps the v4.3.5 runtime protection and adds targeted warning-level diagnostic logging for packets that reach the generator runtime decoder.

## Added

- Logs the generator runtime decode decision for each runtime candidate:
  - accepted
  - decreasing
  - implausibly_high
  - implausible_jump
- Logs nearby 16-bit candidate byte windows so we can determine whether the runtime is being decoded from the wrong packet or wrong offset.
- Includes raw packet length, status byte, status word, decoded candidate, previous accepted runtime, and full raw packet hex.

## Notes

This is intentionally a short-term diagnostic build. It may produce repeated warning-level log lines while installed. Once the bad packet pattern is identified, the diagnostic trace should be removed or demoted back to debug level.
