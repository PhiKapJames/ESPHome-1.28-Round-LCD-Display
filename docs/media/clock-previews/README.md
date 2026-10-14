# Clock face preview renders

Lossless 240x240 PNG captures of every clock face **as the device renders
them**, produced by the host-platform snapshot harness in
`tests/host-clock-preview.yaml` (see `docs/VALIDATION.md`). No hardware is
involved: the frames come from the same renderer code and fonts that firmware
runs.

- `lineup.png` — the full seven-face release lineup in one sheet.
- `original.png`, `classic_analog.png`, `modern_dashboard.png`,
  `fitness_ring.png`, `clean_arc.png`, `minimalist.png`,
  `weather_station.png` — individual current renders.
- `face-off-0.7.3-vs-0.8.0.png` — main 0.7.3 designs next to the 0.8.0 faces
  for the faces that existed in 0.7.3, showing what changed.

These images are documentation snapshots, not golden-image tests; regenerate
them whenever a face changes (commands in `docs/VALIDATION.md`).
