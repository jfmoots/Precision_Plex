# Precision Plex v5.5.11 — Authoritative Carefree Flip Completion

This release preserves the Patio Awning's synthetic 100% position after the
entire configured smart-open sequence finishes.

## Smart-open endpoint

The sequence remains:

1. Detect arm lock from motor current.
2. Run the configured extension overrun.
3. Stop extending.
4. Run the configured Fabric Tighten retract.
5. Stop retracting and report 100% extended.

The endpoint hold now waits for authoritative PID32/02BB controller telemetry
to confirm both motion directions idle. Clearing the local provisional command
overlay can no longer release the hold early and allow delayed retract telemetry
to reduce the reported position.
