# AGENTS.md

## Purpose

This repository provides reusable ESPHome YAML packages for 240x240 GC9A01A
1.28-inch round LCD displays. It keeps shared display logic, hardware profiles,
renderers, and optional camera-alert logic public while keeping each
installation's Home Assistant entities, network details, and credentials private.

## Architecture rule: packages, not external_components

Use ESPHome `packages:` for this repository.

Do **not** migrate this project to `external_components:` unless the repository
later adds a real custom ESPHome component implementation under a supported
component directory structure. `external_components` is for custom ESPHome
Python/C++ components; this project distributes reusable YAML configuration.

Remote package files may intentionally be included more than once with different
`vars`. ESPHome explicitly supports this pattern and this project depends on it
for per-device page and camera instances.

## Repository layout

- `packages/`: shared scheduler, display core, renderers, theme, clock, camera
  engine, and reusable page/camera-source templates.
- `hardware/`: processor/memory/display hardware definitions.
- `profiles/`: composable entrypoints combining shared packages with a hardware
  target and optional features.
- `examples/`: public placeholder configurations only.
- `tests/`: synthetic validation/compile configurations only.
- `docs/`: architecture, configuration, release, and validation guidance.
- `scripts/`: repository/privacy/structure checks.

## Public/private boundary

Never commit installation-specific or sensitive values.

Keep these in the user's private/local ESPHome YAML or `secrets.yaml`:

- real Home Assistant entity IDs when they identify the user's installation;
- Home Assistant IP addresses, hostnames, or origins;
- Wi-Fi SSIDs/passwords;
- API encryption keys;
- OTA authentication material, including passwords or encryption keys;
- access tokens, camera tokens, cookies, or credentials;
- private site/device mappings;
- generated firmware binaries containing credentials.

Public examples and tests must use obviously synthetic placeholder values.

Remote packages must not contain `!secret` lookups. Expose configurable public
defaults/substitutions and let the private device YAML provide real values.

## Device YAML ownership

The private device YAML is the composition layer. It selects:

1. one hardware/profile entrypoint;
2. zero or more reusable page templates;
3. zero or more reusable camera-source templates;
4. private Home Assistant entity mappings and credentials.

Do not move concrete household/site page lists into a public profile merely to
shorten a private YAML. The repeated `files:` entries are intentional: each
instance supplies its own `vars` while the renderer stays centralized.

Example:

```yaml
packages:
  round_display:
    url: https://github.com/PhiKapJames/ESPHome-1.28-Round-LCD-Display
    ref: main
    files:
      - profiles/esp32-c3-camera.yaml
      - path: packages/page-numeric.yaml
        vars:
          page_id: room
          page_label: Room
          page_entity: sensor.example_room_temperature
          page_duration_ms: "8000"
          page_order: "10"
          page_unit: °F
          page_suffix: °
          page_decimals: "1"
          page_panel_style: "1"
          page_color_red: 0%
          page_color_green: 62%
          page_color_blue: 45%
```

For active development, `ref: main` plus a reasonable refresh interval is
acceptable. For stable deployments, prefer a tested release tag or immutable
commit SHA; `refresh: never` is appropriate for an intentionally pinned ref.

## Page-template conventions

- A reusable page belongs in `packages/page-*.yaml`.
- Each template instance must have a unique ESPHome-safe `page_id`.
- Keep site-specific entity IDs in the private device YAML.
- Register normal rotation pages through the shared runtime registry.
- Register a matching human-readable entry in `rotation_labels` so page-aware
  display profiling stays aligned with the sorted page registry.
- Preserve `page_order` and per-page duration behavior.
- The clock remains an interstitial page managed by shared code.
- Preserve `clock_face_style` as the per-device selector. Supported values are `original`, `classic_analog`, `modern_dashboard`, `fitness_ring`, and `clean_arc`; `original` must remain the backward-compatible default unless explicitly changed.
- Camera alerts interrupt rotation and are not normal rotation pages unless
  `packages/page-camera.yaml` is explicitly instantiated.
- Trend lines/sparklines are intentionally removed. Do not reintroduce them
  unless explicitly requested.
- Preserve the current bold, high-contrast round-display layout and page
  indicator behavior unless a design change is explicitly requested.

## Camera conventions

- Use one `packages/camera-source.yaml` instance per configured source.
- `camera_id` values must be unique and ESPHome-ID-safe.
- Person and vehicle triggers are independently configurable.
- A source may be person-only, vehicle-only, both, or manual-only.
- Alert snapshots interrupt the playlist; they do not silently become normal
  rotation pages.
- Do not log token-bearing snapshot URLs.
- Preserve heap/contiguous-memory safeguards and queue/cooldown behavior unless
  the change is deliberate and tested.
- Automatic alerts have three lifetime controls: minimum hold, detector-clear
  delay, and a shared hard maximum that can be overridden per camera. Preserve
  manual snapshot duration as a separate fixed setting.
- Optional periodic refresh must remain serial: never overlap JPEG downloads or
  discard the last good frame merely because a refresh fails.

## ESPHome compatibility

The repository currently targets ESPHome 2026.9.0 or newer. Before adopting a
new ESPHome feature or syntax:

1. verify it against current official ESPHome documentation;
2. prefer native ESPHome capabilities over custom C++/Python;
3. avoid deprecated syntax;
4. keep hardware differences explicit rather than hiding warnings;
5. update CI/test fixtures when the minimum supported version changes.

Do not convert reusable YAML into an external component simply because
`external_components` exists.

## Display/runtime invariants

- `LCD Backlight` is the authoritative display-enabled gate. OFF suspends
  rotation/redraw/camera-display work but leaves networking, Home Assistant,
  time, and diagnostics online.
- The shared UI clock uses Home Assistant time with ID `ha_time`. A private
  device may add a separate SNTP source for local schedule enforcement.
- Normal rotation display updates go through `profiled_display_update`.
  The physical `main_display.update()` is deferred onto `main_display` so
  ESPHome attributes blocking time to the display component instead of
  `display_rotation`.
- The profiler threshold is controlled by `display_profile_warn_ms` (default
  50 ms). Slow normal-rotation updates log their page label under
  `round_minion.display`; the shared clock label is `clock`.
- Do not reintroduce direct `component.update: main_display` calls into the
  normal rotation path. Camera-alert rendering has its own update path.
- Display suspension and camera takeover must cancel a pending profiled normal
  update before changing pages, preventing stale deferred draws.

## Validation requirements

For meaningful changes:

1. run `scripts/check_public.py` and `scripts/check_project.py`;
2. validate the affected synthetic ESPHome configurations;
3. compile representative hardware profiles when CI supports them;
4. for public-repo changes, inspect the 10-profile GitHub Actions matrix and do
   not merge while any required config/compile job is failing;
5. preserve the CI guard that rejects unresolved-substitution warnings;
6. test on one physical device before broad rollout when hardware behavior may
   change.

Do not suppress compiler/ESPHome warnings as a substitute for fixing the cause.

## Editing guidance for agents

- Read this file, `README.md`, and `docs/CONFIGURATION.md` before architectural
  changes.
- Prefer small, composable package changes over duplicating renderer logic.
- Keep IDs deterministic and unique after template expansion.
- Preserve backwards compatibility for established substitutions when practical.
- Update documentation/examples whenever public configuration syntax changes.
- Update `esphome.project.version` and release notes for a versioned behavioral
  release.
- Never claim hardware validation unless it was actually performed.
- Do not commit private user configuration supplied in chat/issues.
- If a requested change conflicts with the public/private boundary, keep the
  reusable mechanism public and provide the private YAML change separately.

## Source-of-truth references

Use current official ESPHome documentation as the source of truth, especially:

- https://esphome.io/components/packages/
- https://esphome.io/components/external_components/
- https://esphome.io/components/substitutions/
- https://esphome.io/components/display/mipi_spi/

When docs and old repository comments disagree, follow current official
documentation and update repository documentation accordingly.
