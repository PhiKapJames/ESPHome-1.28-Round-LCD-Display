# Changelog

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
