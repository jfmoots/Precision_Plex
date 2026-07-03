## Precision Plex v5.3.8 — BLE Packet Forensics

This release builds directly on the v5.3.7 BLE Session Hardening work by adding deeper packet-forensics diagnostics. v5.3.7 proved that malformed or misaligned BLE packets were occasionally being rejected before they could corrupt Home Assistant entity state. v5.3.8 adds the visibility needed to understand exactly what those rejected packets look like.

### New Diagnostics

- Added **BLE Last Rejected Packet** diagnostic sensor.
- Added **BLE Last Rejected Packet Length** diagnostic sensor.
- Added **BLE Packet Rejection Percent** diagnostic sensor.
- Expanded rejected-packet attributes with:
  - Last rejected packet type
  - Last rejected packet source
  - Last rejected packet sender
  - Last rejected packet length
  - Last rejected packet hex
  - Last rejected 02AA hex
  - Last rejected 02BB hex
  - Reject reason counts
  - Packet length counts
  - Packet type counts

### New Diagnostic Button

- Added **Reset BLE Diagnostics** button.
- This resets BLE health counters without disturbing current Precision Plex telemetry state.

### Why This Matters

The goal is to distinguish between occasional RF noise, malformed BLE notifications, shifted Precision Plex frames, and valid-looking packets with impossible values. This should make future BLE reliability improvements much more targeted and much less speculative.

### Packaging

- Manifest version updated to `5.3.8`.
- Custom brand assets remain in `custom_components/precision_plex/brand/` only.
- No invalid `custom_components/brand/` folder.
- No `__pycache__` or `.pyc` files included.

### Rejected Packet Forensics Buffer

v5.3.8 now keeps a rolling buffer of the most recent 100 rejected BLE packets. The buffer is exposed through the new **BLE Rejected Packet Log** diagnostic sensor and included in Home Assistant diagnostics exports.

Each captured rejected packet entry includes:

- Timestamp
- Packet type
- Reject reason
- Notification source
- Sender handle
- Packet length
- Raw hex payload

This allows field failures to be reviewed later without needing debug logging enabled before the issue occurs.
