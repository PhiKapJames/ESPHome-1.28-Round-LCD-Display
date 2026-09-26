# Release notes and current source state

The current source version is **0.6.9**. The `esphome.project.version` value
describes the source/firmware behavior; it does not by itself imply that a
matching GitHub release tag exists. For the complete version-by-version history,
see the [changelog](../CHANGELOG.md).

## Current 0.6.9 architecture

- ESPHome **2026.9.0 or newer** is required. CI is pinned to
  `ghcr.io/esphome/esphome:2026.9.0`.
- The project is reusable ESPHome YAML delivered through `packages:`; it is not
  an `external_components:` repository.
- Private device YAML owns device identity, Home Assistant entity mappings,
  network settings, API/OTA authentication, schedules, and secrets.
- Normal content uses an ordered runtime registry populated by repeated
  `page-numeric.yaml`, `page-battery.yaml`, and optional
  `page-camera.yaml` template instances. There is no fixed page-count limit in
  shared code.
- The clock remains a shared interstitial page with five selectable renderers:
  `original`, `classic_analog`, `modern_dashboard`, `fitness_ring`, and
  `clean_arc`.
- Numeric and battery pages intentionally omit trend/history graphs.
- The `LCD Backlight` switch is the display-enabled gate. Turning it OFF stops
  rotation/redraw/camera-display work while networking, Home Assistant, time,
  and diagnostics remain online.
- Normal rotation updates are page-profiled. Slow updates log the page label and
  full render+flush duration under `round_minion.display`; the default threshold
  is 50 ms. The physical update is deferred onto the MIPI display component so
  ESPHome's stock blocking warning is attributed to display work rather than
  `display_rotation`.
- Camera alerts are separate from normal rotation unless a
  `page-camera.yaml` instance is explicitly added. Each source has its own
  Alerts switch and manual snapshot button.
- Automatic camera alerts support person, vehicle, both (OR), or manual-only
  sources. They have a minimum hold, detector-clear delay, and a shared hard
  maximum that can be overridden per source. Optional refresh remains serialized
  and retains the last good image on refresh failure.
- Camera token/origin validation, queue limits, cooldowns, download timeout, and
  heap/contiguous-memory guards remain in the shared camera engine.

## Hardware profiles

- **ESP32-C3:** 160 MHz, 4 MB flash, no PSRAM, 8-bit color, 50% framebuffer.
- **ESP32-C6:** 160 MHz, 4 MB flash, no PSRAM, 8-bit color, 50% framebuffer,
  native USB Serial/JTAG logging, and a separate reference GC9A01 pin map.
- **ESP32-S3 quad-PSRAM:** 240 MHz, 4 MB flash, quad PSRAM at 80 MHz, 16-bit
  color, full framebuffer, and the optimized high-quality battery keyline.

Base and camera-enabled profile variants exist for C3, C6, and S3. The S3
quad-PSRAM profile must not be used on an S3 module whose PSRAM/flash
configuration has not been confirmed.

## Validation state

GitHub Actions validates and compiles 10 synthetic profiles across C3, C6, and
S3. Every matrix job runs the repository privacy/structure checks,
`esphome config`, and a full `esphome compile`. The config step also rejects
unresolved-substitution warnings.

Synthetic CI proves source/configuration/toolchain compatibility. It does not
replace validation of a private device YAML or physical-device testing. See
[validation](VALIDATION.md) for the exact matrix and local commands, and
[configuration](CONFIGURATION.md) for the public settings contract.

## Important upgrade milestones

- **0.5.0:** replaced the fixed six-slot model with the ordered template-driven
  runtime page registry.
- **0.5.1:** added ESP32-C6 profiles and C6-safe reference display wiring.
- **0.6.0:** added selectable clock faces.
- **0.6.2:** added optional serialized camera refresh with ping-pong image slots.
- **0.6.3:** made LCD Backlight the authoritative display suspension gate.
- **0.6.4:** made automatic camera-alert lifetime follow detector state.
- **0.6.5:** renamed the shared Home Assistant time ID to `ha_time`, added
  configurable backlight restore behavior, and refreshed validation guidance.
- **0.6.6:** removed spurious conditional camera-trigger substitution warnings
  and added a CI guard against their return.
- **0.6.7:** added the global/per-camera automatic alert maximum.
- **0.6.8:** reduced repeated framebuffer work in numeric, battery, and clock
  renderers without lowering S3 display quality.
- **0.6.9:** added page-aware normal-rotation display profiling and moved the
  physical normal-page update onto the display component's scheduler context.

## Historical v0.1.0 migration note

Version 0.1.0 was the original public-safe source extraction of the established
GC9A01A display configuration. Its goals were to separate private identity,
Home Assistant mappings, credentials, and origins from reusable display code;
provide C3 and S3 profiles; preserve the established page geometry and
detection-only snapshots; remove trend/history graph components; and introduce
synthetic CI plus privacy checks.

That original release note described the repository as a **source migration
candidate** and explicitly did not claim that offline checks proved an ESPHome
compile or physical-device pass. Those statements remain historically accurate,
but they no longer describe the current 0.6.9 feature set or CI coverage.
