# Precision Plex v4.3.4 - Quiet Generator Runtime Guard

This maintenance release keeps the v4.3.3 generator runtime protection but prevents normal bad telemetry samples from spamming the Home Assistant log.

## Fixed

- Demotes ignored decreasing generator runtime samples from warning/error-level logging to debug logging.
- Changes the generator runtime sensor state class from `total_increasing` to `measurement` so Home Assistant Recorder does not complain when the Precision Plex telemetry occasionally reports a bogus lower runtime value.
- Keeps the runtime guard in place so the displayed runtime is not overwritten by obvious decreasing samples during a running session.

## Retained

- v4.3.2 HomeKit exposure cleanup.
- v4.3.x HomeKit-friendly humidity percentage helper sensors for Fresh Water, Grey Water, Black Water, and Propane.

## Packaging

- Built without `__pycache__` directories or `.pyc` files.
