# Changelog

## 0.6.8 — 2026-09-26

- Reduced display-render framebuffer work without lowering S3 color depth, full-buffer mode, or 80 MHz LCD SPI rate.
- Replaced overlapping rounded-box construction on numeric/battery pages with single-pass scanline fills.
- Replaced frequent small filled-circle arc markers with equivalent non-overlapping scanline dots.
- Reworked the S3/high-quality battery value keyline from eight offset 84 px font renders to one glyph-restricted bold underlay plus the regular white value.
- Reworked the original clock's large digit cleanup to erase only ring pixels crossing the text fields instead of filling large black rectangles.
- Preserved C3/C6 four-direction battery keyline behavior.
- Added structural regression checks for the optimized renderer paths.

## 0.6.7 — 2026-09-26

- Added a shared automatic-alert hard maximum through `camera_max_hold_ms`, defaulting to `30000` ms.
- The maximum is measured from the first successful image/hold phase, so initial download time does not consume the visible hold budget.
- Individual camera-source entries can override the shared maximum by supplying `camera_max_hold_ms` in that entry's `vars`.
- A per-camera value of `0` disables the hard cap for that source.
- The hard maximum wins over a detector that remains ON or a clear-delay tail that would otherwise extend past the limit.
- Manual snapshot duration remains controlled only by `camera_hold_time`.
- Added an INFO log when an automatic alert ends because its maximum hold was reached.
- Added CI coverage for inherited, overridden, and unlimited per-camera maximum values.

## 0.6.6 — 2026-09-26

- Reworked optional camera detector package selection to use ESPHome's supported conditional `!include` filename pattern.
- Removed the intermediate `_person_trigger` / `_vehicle_trigger` IncludeFile substitutions that produced spurious unresolved-variable warnings during config parsing and remote builds.
- Preserved existing behavior: disabled detector types still create no Home Assistant subscription, and enabled detectors retain the same press/release lifetime tracking.
- Added structural coverage for dynamic package include filenames.
- GitHub Actions now fails the config-validation step if ESPHome reports `Could not resolve substitution variable`, preventing this warning class from silently returning.

## 0.6.5 — 2026-09-26

- Renamed the shared Home Assistant time component ID from the misleading `sntp_time` to `ha_time`; the time platform remains Home Assistant.
- Added `backlight_restore_mode` with the existing `ALWAYS_ON` default, allowing scheduled devices to opt into `ALWAYS_OFF` privately.
- Documented the intentional direct use of the public ESP-IDF heap-capability API for camera RAM guards and heap diagnostics.
- Clarified that ESPHome 2026.9.0 requires Python 3.12+ for native installs and that the pinned Docker image avoids host-Python coupling.
- Updated validation documentation to describe the current 10-profile GitHub Actions config/compile matrix instead of retired six-slot-era checks.
- Added regression coverage for the Home Assistant time ID and backlight restore-mode override.

## 0.6.4 — 2026-09-25

- Added per-camera detector state tracking for automatic person/vehicle alerts.
- Automatic alerts now remain visible for at least `camera_min_hold_time` (default `7s`), continue while any enabled detector for that camera is ON, then remain visible until every enabled detector has stayed OFF for `camera_clear_delay` (default `2s`).
- Detector reactivation during the clear delay cancels the pending exit and restarts the clear delay after the next OFF transition.
- Person + vehicle sources use combined OR lifetime semantics: either active detector keeps the alert visible.
- Manual snapshot requests retain the existing fixed `camera_hold_time` behavior.
- Display OFF still cancels alerts immediately and releases camera resources.

## 0.6.3 — 2026-09-25

- Made the shared `LCD Backlight` switch the authoritative display-enabled gate, independent of whether Home Assistant or a local schedule changes it.
- Stopped page rotation and display redraw activity while the backlight switch is OFF; turning it ON starts a clean normal rotation.
- Added an extensible display-suspend callback path so optional feature packages can release resources without making the base profile depend on them.
- Camera alerts and manual snapshot requests are ignored while the display is OFF.
- Turning the display OFF during an active camera alert stops the alert/refresh scripts and releases both decoded image slots.
- Optional normal-rotation camera pages now avoid redraws/download startup while the display is OFF.
- Wi-Fi, Home Assistant subscriptions, time, Tailscale/other networking, and diagnostics remain active; this is display suspension, not deep sleep.

## 0.6.2 — 2026-09-25

- Added optional periodic alert-camera refresh through `camera_refresh_interval_ms`; the default `'0'` preserves existing single-snapshot behavior.
- Added ping-pong decoded-image slots so the current good frame remains visible while the next still downloads.
- Kept JPEG requests strictly serial with no overlapping downloads.
- Refresh errors and timeouts now keep the last good frame on screen instead of replacing it with an error screen.
- Intended 1 Hz usage on PSRAM-equipped S3 devices can be enabled privately with `camera_refresh_interval_ms: '1000'`.

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
