# Precision Plex v5.3.2 — Smart Awning Tuning + Current-Drop Retract

This test build refines the Smart Awning current-sensing behavior validated on the Georgetown GT5 coach.

## Changes

- Changes the default Smart Awning extend overrun to 100 ms.
- Changes the default Smart Awning fabric-tighten / Carefree Flip time to 4000 ms.
- Extends the smart awning safety timeout so retract is not cut short by the old close timer.
- Smart retract now treats the factory power cut / current drop-to-zero as the normal closed signal.
- Smart retract only forces position to 0% when the current-drop close signal is actually observed.
- Smart extend continues to force position to 100% after arm-lock detection and the flip sequence.
- Slides remain on the existing timed/quadrature paths.

## Test Focus

1. Confirm slides still extend, retract, and stop normally.
2. Confirm HA Open performs arm-lock detection and the Carefree Flip.
3. Confirm HA Close continues until the awning fully seats and current drops near zero.
4. Confirm awning position reports 100% after smart open and 0% after smart close.
