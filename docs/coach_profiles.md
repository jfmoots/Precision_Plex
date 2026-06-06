# Coach Profiles

Precision Plex v4.1.0 introduces a coach profile foundation. A coach profile contains the BLE command payloads, decoded 02BB state-bit mappings, and profile metadata for a specific RV layout.

## Default Profile

The default profile is:

```text
georgetown_gt5_34m5
```

It lives at:

```text
custom_components/precision_plex/profiles/georgetown_gt5_34m5.py
```

This profile contains the mappings that were previously hardcoded in v4.0.3. v4.1.0 intentionally keeps this profile active by default so existing Georgetown GT5 34M5 installs keep the same behavior.

## Future Profiles

Future coach profiles should define the same structure and be registered in:

```text
custom_components/precision_plex/profiles/__init__.py
```

The integration currently loads the default Georgetown GT5 34M5 profile. Profile selection can be added later after additional coach layouts have known-good mappings.
