# Precision Plex v4.1.0 — Coach Profile Foundation

v4.1.0 introduces the first coach profile architecture for the Precision Plex Home Assistant integration.

## What Changed

- Added a `profiles/` package for coach-specific mappings.
- Moved the Georgetown GT5 34M5 command and state-bit mappings into `profiles/georgetown_gt5_34m5.py`.
- Kept the Georgetown GT5 34M5 profile as the default active profile.
- Preserved the existing v4.0.3 entity names, unique IDs, commands, state bits, and timing behavior.
- Added active coach profile information to Home Assistant diagnostics.
- Bumped the integration version to `4.1.0`.

## Compatibility

This is intended to be a low-risk refactor release. It should behave the same as v4.0.3 on the tested Georgetown GT5 34M5 coach.

## Why This Matters

Coach profiles make it possible to support additional Precision Plex RV floorplans in the future without mixing all command mappings and telemetry definitions into the core integration code.
