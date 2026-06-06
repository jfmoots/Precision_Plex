# Precision Plex Home Assistant Integration v4.5.1

## Telemetry Sanity Guard Follow-Up

v4.5.1 is a focused stability follow-up to v4.5.0.

After the v4.5.0 telemetry validation release, additional startup-history review showed that a small number of short-lived propane changes could still appear when the Wireless TP stream emitted clean-looking but incorrect LP samples. This release tightens the telemetry guardrails without reintroducing noisy diagnostic logging.

## Changes

### Stronger 02AA Frame Shape Validation

The 02AA telemetry decoder now rejects frames that do not match the known fixed-position frame shape for the tested coach.

Additional whole-frame checks include:

- Enforcing the expected 20-byte 02AA telemetry frame length
- Rejecting known shifted frames with trailing `0x55`
- Rejecting frames with an invalid fresh-tank framing nibble
- Retaining existing grey/black framing nibble checks
- Retaining voltage plausibility checks

Malformed frames are discarded before any telemetry entities are updated.

### LP / Propane Stability Improvement

LP telemetry validation now includes confirmation for changed clean LP values.

The first valid LP value still populates immediately at startup. After that, a changed clean LP value must be observed in consecutive accepted frames before it is published.

This prevents brief one-sample `0%` or `25%` propane blips from appearing when the Wireless TP stream emits transient but clean-looking LP samples.

Existing LP validation remains in place:

- Known-good LP encodings are accepted
- Dirty LP bytes with non-zero low nibbles are rejected
- Last-known-good propane value is retained when LP telemetry is invalid

### Logging Cleanup

Startup subscription messages for the 02AA and 02BB notification streams remain informational and are no longer treated as warnings.

Noisy overnight diagnostic frame logging remains removed from production builds.

## Summary

v4.5.1 keeps the telemetry validation foundation introduced in v4.5.0 and adds another layer of protection against brief malformed or misleading Wireless TP telemetry samples.
