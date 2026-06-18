# Precision Plex v5.3.3 — Smart Awning Open Fix

Fixes a smart awning open-path NameError caused by retract-only current-drop handling being referenced during the open sequence.

Includes prior smart awning tuning from v5.3.2:
- 100 ms extend overrun default
- 4000 ms fabric tighten default
- Smart retract current-drop handling
- Position forced after smart current-sense completion

Package excludes __pycache__ and .pyc files.
