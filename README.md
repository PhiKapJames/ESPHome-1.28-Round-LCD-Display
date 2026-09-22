# HA ESP Round Minions

Reusable ESPHome packages for 240 × 240 GC9A01A round displays connected to
Home Assistant. Keep shared display code here; keep actual device names,
entity mappings, Home Assistant origins, Wi-Fi credentials, API keys, and OTA
passwords in local ESPHome configuration files.

**Version: 0.1.0 — source migration candidate.** The package structure has been
checked offline. The initial package extraction has not yet been compiled as ESPHome
firmware in the preparation environment. The included GitHub Actions workflow runs actual ESPHome validation
and compilation after publication. Check those results and validate your local
configuration before installing. See [validation](docs/VALIDATION.md).

## What it displays

- Up to five numeric/temperature pages and one optional battery-percentage page.
- Large centered readings, rounded panels, location accents, real 12-hour graphs,
  and page-position dots with an active halo.
- A shared large-font clock between each enabled content page.
- A horizontal battery silhouette filled from the reported percentage.
- Optional detection-only camera snapshots, center-cropped to fill the round LCD.
  Camera pages never join the regular playlist or add a page dot.
- A **Show Camera Snapshot** Home Assistant button: a manual/automation override.
  It bypasses the automatic-alert switch/cooldown, not readiness or RAM checks.
- Alerts save the current page and its remaining duration, then resume afterward.

This initial package release preserves the established rendering geometry and
snapshot behavior. It is not a new visual theme or a performance optimization.

## Installation

Requires **ESPHome 2026.9.0 or newer**. The initial CI image is pinned to
`ghcr.io/esphome/esphome:2026.9.0`. Newer builders should be tested before updating
all devices. Packages are downloaded by the builder at build time; devices do
not pull YAML from GitHub and do not update merely because this repo changes.

1. Copy [the example](examples/device.example.yaml) into your **local** ESPHome
   configuration directory. Do not enter real settings in the public example.
2. Set the hardware profile and actual entities in that local file.
3. Preserve the existing device `name`, API key, and OTA password during migration.
4. Run ESPHome **Validate**, then compile and install on one device first.
5. Test every enabled metric, battery fill, clock, snapshot override, detection,
   failed download, and return to the interrupted page.

Load the camera-enabled C3 profile from this repository:

```yaml
packages:
  round_minion:
    url: https://github.com/PhiKapJames/HaEspRoundMinions
    ref: main  # Use a tested commit SHA for a pinned deployment.
    files:
      - profiles/esp32-c3-camera.yaml
    refresh: 1d
```

For a local trial, copy this project directory beside your
private device YAML and instead use:

```yaml
packages:
  round_minion: !include HaEspRoundMinions/profiles/esp32-c3-camera.yaml
```

Do not use both package forms at once. A public GitHub token is not needed for
an ESPHome builder to read a public repository. Firmware binaries containing
real credentials must stay private.

## Hardware profiles

| File | Hardware and memory | Camera code |
| --- | --- | --- |
| `profiles/esp32-c3.yaml` | C3, 160 MHz, no PSRAM; 8-bit / 50% buffer | Omitted |
| `profiles/esp32-c3-camera.yaml` | Same C3 settings | Included |
| `profiles/esp32-s3-quad-psram.yaml` | S3, 240 MHz, 4 MB flash, confirmed quad PSRAM at 80 MHz; 16-bit / full buffer | Omitted |
| `profiles/esp32-s3-quad-psram-camera.yaml` | Same S3 quad-PSRAM settings | Included |

The S3 profiles are **not** for every S3 module. Confirm flash capacity, PSRAM
presence, mode, pin assignments, and wiring. Do not select the S3 PSRAM profile
for a C3 or an S3 without the stated memory. Pin defaults match the project's
GC9A01A wiring, not a universal ESP32 pinout.

The default LCD SPI rate is 80 MHz, preserving the established device setting.
If the display corrupts, override `display_spi_rate: 40MHz` locally. PSRAM speed
and LCD SPI speed are separate settings. Never hide timing warnings as a fix.

## Configuration

See [configuration reference](docs/CONFIGURATION.md). Site settings can be shared
with a local package such as `!include minion-sites/site.yaml`. These local site
files and `secrets.yaml` must **not** be uploaded to this repository.

Slots 1–5 accept numeric values with a configurable label, unit suffix, and
number of decimals. Slot 6 is the battery presentation and expects **0–100%**.
Disable a slot with `metric_3_enabled: 'false'`. Disabled slots are removed from
the playlist and page dots and have no Home Assistant subscription. In v0.1.0,
the small per-slot graph allocations are still reserved. All slots cannot be
disabled. The relative order of enabled slots is 1 through 6.

The configured `unit` is metadata, not unit conversion. Home Assistant must
supply the values in the intended units. Add a conversion filter locally when
needed. Adding more than six slots or changing their order is a code change in
this initial release, not a runtime Home Assistant setting.

Camera snapshots use the camera entity's `entity_picture` attribute and its
rotating token. Set `ha_base_url` to the same Home Assistant instance importing
that attribute. Each accepted trigger requests a still; it is not a live stream
or necessarily the exact frame that caused detection. Only the expected camera
proxy path and configured origin are accepted. Token-bearing URLs are not logged
by the project's own logs, and potentially URL-bearing component logs are muted.
Do not enable verbose logging and publish it without redaction.

An HTTP origin means unencrypted image traffic on the LAN. HTTPS requires a
trusted certificate; `verify_ssl: true` is preserved. No administrator token or
camera username/password belongs in this public repository. The native ESPHome
API's encryption does not encrypt the separate HTTP request.

## Repository maintenance

`packages/` holds the shared scheduler, renderers, graph and camera code.
`hardware/` describes the actual processor/memory profile. `profiles/` combines
features. `examples/` and `tests/` contain only placeholders or deliberately
synthetic credentials. `scripts/` provides offline structure and privacy checks.

Use a branch/PR for changes, run CI, test one physical device, then make a new
version tag. Pin deployed devices to a release tag (or immutable commit). Do not
move old tags. Update `esphome.project.version` for each release. Roll back by
selecting the old ref and rebuilding/installing; changing a ref alone does not
alter running firmware. No automated deployment to actual devices is configured.

## Repository status and deployment safety

This repository contains shared source and synthetic examples only. It does not
contain a particular installation's device YAML, real entity mappings, camera
origin, Wi-Fi credentials, or API/OTA secrets. Keep those in local ESPHome files.

The first version is a source migration candidate (project version `0.1.0`), not
a claim of hardware validation. Check the Actions results for the exact commit
before deploying. No release tag is implied by the project version. A deployed
remote package may use a tested full commit SHA, avoiding an assumed tag or a
moving `main` branch. Later tested versions can be tagged through normal GitHub
release management. This repository does not deploy firmware to devices.

For ongoing changes, use a branch and pull request, with successful CI and a
physical-device test before rollout. Never attach real firmware binaries, logs
containing tokens, or private compilation bundles to public issues or releases.

## License and third-party components

Project code is MIT-licensed. ESPHome and its dependencies retain their own
licenses. Google Fonts are downloaded by ESPHome as specified in the YAML; no
font binaries are redistributed here. The battery is a primitive-drawn,
MDI-inspired silhouette, not a bundled icon font or downloaded SVG.

## Primary references

- [ESPHome packages](https://esphome.io/components/packages/)
- [ESPHome substitutions](https://esphome.io/components/substitutions/)
- [MIPI SPI display](https://esphome.io/components/display/mipi_spi/)
- [ESPHome PSRAM](https://esphome.io/components/psram/)
- [Online images](https://esphome.io/components/image/online_image/)
