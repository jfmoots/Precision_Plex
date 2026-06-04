# Precision Plex v4.3.5

## Generator Runtime Outlier Protection

This release improves the generator runtime guard added in the v4.3.x HomeKit cleanup series.

### Fixed

- Prevents implausibly high generator runtime samples, such as thousands of hours, from being accepted as the stored runtime.
- Prevents a bad high sample from causing later legitimate runtime samples to look like decreases.
- Keeps the existing decreasing-sample protection.
- Adds protection against implausible jumps between accepted live telemetry samples.

### Diagnostics

The Generator Runtime sensor now includes diagnostic attributes for the last ignored runtime sample and the reason it was ignored.

### Packaging

- Source-only GitHub/HACS-ready package.
- Excludes `__pycache__`, `.pyc`, and temporary build artifacts.
