# Clock face preview renders

Lossless 240x240 PNG captures of every clock face **as the device renders
them**, produced by the host-platform snapshot harness in
`tests/host-clock-preview.yaml` (see `docs/VALIDATION.md`). No hardware is
involved: the frames come from the same renderer code and fonts that firmware
runs.

- `lineup.png` — the current release lineup in one sheet.
- `original.png`, `classic_analog.png`, `modern_dashboard.png`,
  `clean_arc.png`, `weather_station.png` — individual current renders.
- `face-off-0.7.3-vs-0.8.0.png` — main 0.7.3 designs next to the 0.8.0
  redesigns for the pending per-face design decisions.

These images are documentation snapshots, not golden-image tests; regenerate
them whenever a face changes (commands in `docs/VALIDATION.md`).
