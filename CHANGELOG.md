# Changelog

## 0.6.1 — 2026-09-24

- Fixed the clock renderer so `clock_face_style` is actually expanded by ESPHome instead of being escaped as a literal.
- Added a structural regression check that rejects escaped ESPHome substitutions in the clock renderer.
- No private YAML setting name changed; existing `clock_face_style` values remain valid.

## 0.6.0 — 2026-09-24

- Added selectable clock faces through the `clock_face_style` substitution.
- Preserved the established nested-ring clock as the default `original` style.
- Added `classic_analog`, `modern_dashboard`, `fitness_ring`, and `clean_arc` styles inspired by round smartwatch/instrument layouts.
- Added shared clock fonts needed by the new renderers; no private entities are required.
- Invalid clock style names render an on-screen diagnostic instead of silently selecting a different face.

## 0.5.2 — 2026-09-23

- Removed trend/history lines from all reusable numeric and battery pages.
- Removed the underlying ESPHome graph components rather than only hiding them.
- Removed obsolete graph interval/color settings from examples, tests, and configuration documentation.
- Preserved the existing panels, arcs, primary readings, clock placement, and page-position indicators.

## 0.5.1 — 2026-09-23

- Added ESP32-C6 4 MB/no-PSRAM base and camera-enabled profiles.
- Added an explicit C6 target/variant, native USB Serial/JTAG logging, and a reference GC9A01 pin map that avoids C6 strapping, USB, UART0, and flash-reserved pins.
- Added synthetic ESPHome validation/compile coverage for C6 base and camera configurations.
- Kept C6 on the conservative 8-bit/50% framebuffer path; no Bluetooth or IEEE 802.15.4 feature is enabled by default.

## 0.5.0 — 2026-09-22

- Replaced the fixed six-slot scheduler with an ordered dynamic page registry.
- Added reusable numeric, battery, and optional camera rotation-page templates.
- Removed the fixed metric_1..metric_6 slot model entirely; all content pages are explicit templates.
- Added an independent Alerts switch for every camera source and removed the global master alert switch.
- Added a compact Last Camera Alert diagnostic; engine progress status is internal.
- Added CI coverage for 10 numeric + 1 battery + 1 camera rotation page.

## 0.1.0 — 2026-09-22

Initial public-safe package extraction. See [release notes](docs/RELEASE_NOTES.md).
No visual redesign or camera performance claim accompanies this migration.
