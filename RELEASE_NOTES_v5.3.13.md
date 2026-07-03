# Precision Plex v5.3.13 – Smart Awning Diagnostic Logging

This diagnostic build adds detailed INFO-level logging around the Smart Current Sense awning state machine.

No intentional behavior changes are included. The goal is to capture exactly where an awning extend sequence starts, detects arm lock, stops extension, performs the Carefree Flip, and completes.

Use this build when troubleshooting intermittent awning extend/flip behavior. After installing, perform one awning open and download the Home Assistant log.
