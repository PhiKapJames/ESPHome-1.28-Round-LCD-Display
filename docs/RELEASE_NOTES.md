# v0.1.0 — source migration candidate

Extract the established GC9A01A display into public-safe ESPHome packages.

- Separate private identity, HA entity mappings, credentials, and origins.
- Provide C3 and S3 quad-PSRAM profiles, with and without camera support.
- Preserve metric-panel and battery geometry, clock, active-dot halo, and
  detection-only full-screen snapshots with a manual/automation override.
- Parameterize labels, units, slot visibility, pin mappings, and page durations.
- Keep graph `continuous` under `traces`, not at graph level.
- Include synthetic CI examples, actual ESPHome config/compile workflow, privacy
  checks, and public-safe example configuration.

This is initially a source migration candidate; no release tag is implied. Offline checks do not establish an ESPHome
compile or a physical-device pass. Require passing CI and a single-device
migration test before fleet rollout. The known synchronous rendering/download
warnings are not suppressed or claimed to be solved by this packaging change.
