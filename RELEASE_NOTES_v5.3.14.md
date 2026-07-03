# Precision Plex v5.3.14 – Smart Awning Diagnostic Logging Fix

Fixes a diagnostic logging regression introduced in v5.3.13 that could abort the Smart Awning open sequence after arm-lock detection and before the Carefree Flip.

## Fixed
- Removed an invalid close-runner diagnostic log line from the smart-open path.
- Restored the Carefree Flip sequence after arm-lock detection.
- Added a Carefree Flip completion log entry.
- Manifest updated to 5.3.14.

No intended behavior changes beyond restoring the interrupted smart-open sequence.
