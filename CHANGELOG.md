# Changelog

## 0.5.0 — 2026-09-22

- Added opt-in template-driven rotation profiles with repeatable numeric,
  battery, and camera page templates.
- Removed the six-page ceiling for template-profile builds; CI includes a
  10-numeric + 1-battery C3 fixture.
- Added a per-camera automatic alert switch for every reusable camera source.
- Replaced transient Camera Alert Status with persistent Last Camera Alert
  state such as `FRONT: Person`.
- Added optional camera pages to normal rotation while reusing the shared JPEG
  buffer; real alerts preempt those pages.
- Kept existing legacy Camper/Home rotation profiles for backward compatibility.

## 0.1.0 — 2026-09-22

Initial public-safe package extraction. See [release notes](docs/RELEASE_NOTES.md).
No visual redesign or camera performance claim accompanies this migration.
