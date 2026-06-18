# Precision Plex v5.3.5 — Smart Awning Close Seat Detection

This test build changes smart awning close detection from current-drop-to-zero to sustained retract seat high-current detection.

## Changes

- Smart close now stops on the configured Awning Retract End Threshold.
- Adds an extra redundant retract release command after smart close exits.
- Keeps a long safety timeout as fallback only.
- Leaves slide cover paths unchanged.

## Test Focus

- HA Close should retract fully and stop without requiring the manual Stop button.
- HA Open / Carefree Flip should still behave as tuned.
