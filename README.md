# HA ESP Round Minions

Reusable ESPHome packages for 240 × 240 GC9A01A round displays connected to
Home Assistant. Keep shared display code here; keep actual device names,
entity mappings, Home Assistant origins, Wi-Fi credentials, API keys, and OTA
passwords in local ESPHome configuration files.

**Version: 0.5.0 — template rotation candidate.** The package structure has been
checked offline. The initial package extraction has not yet been compiled as ESPHome
firmware in the preparation environment. The included GitHub Actions workflow runs actual ESPHome validation
and compilation after publication. Check those results and validate your local
configuration before installing. See [validation](docs/VALIDATION.md).

## What it displays

- Legacy profiles keep the established five numeric/temperature pages plus one
  battery page for compatibility. New template profiles remove that numbered
  slot limit: repeat numeric, battery, or optional camera page templates as needed.
- Large centered readings, rounded panels, location accents, real 12-hour graphs,
  and page-position dots with an active halo.
- A shared large-font clock between each enabled content page.
- A horizontal battery silhouette filled from the reported percentage, with
  red/yellow/cyan/green charge bands and a high-contrast outlined value.
- Optional detection-only camera snapshots from reusable camera-source package
  instances. There is no hard-coded camera count: add another instance in the
  device's private package list. Each source can trigger on person, vehicle,
  both (OR), or neither/manual-only. Single-lens and multi-lens cameras are
  treated the same; configure the HA camera entity whose image you want.
  Camera pages never join the regular playlist or add a page dot.
- A manual/automation snapshot button and an independent **<Camera> Alerts**
  configuration switch for every camera source. A global Camera Alerts switch
  remains as the master control. Manual snapshots bypass automatic enable/cooldown,
  not readiness or RAM checks.
- A **Last Camera Alert** diagnostic records only the latest automatic event in
  short form such as `FRONT: Person` or `DRIVEWAY: Vehicle`.
- Alerts save the current page and its remaining duration, then resume afterward.

Version 0.5.0 preserves the established legacy rendering geometry and snapshot behavior
while reducing avoidable render work: static arc coordinates are precomputed,
the minute marker uses a lookup table, and the redundant once-per-minute forced
redraw is removed.

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

Load the camera-enabled C3 profile and one or more reusable camera
sources from the same remote package. ESPHome supports including the same remote
file repeatedly with different `vars`:

```yaml
packages:
  round_minion:
    url: https://github.com/PhiKapJames/HaEspRoundMinions
    ref: main  # Pin a tested commit SHA in deployed device files.
    files:
      - profiles/esp32-c3-camera.yaml
      - path: packages/camera-source.yaml
        vars:
          camera_id: driveway
          camera_entity: camera.example_driveway
          camera_source_label: DRIVEWAY
          camera_status_label: driveway
          camera_button_name: Show Driveway Snapshot
          camera_trigger_person: 'true'
          camera_person_entity: binary_sensor.example_driveway_person
          camera_trigger_vehicle: 'true'
          camera_vehicle_entity: binary_sensor.example_driveway_vehicle
          camera_cooldown_ms: '60000'
    refresh: 1d
```

Add another `packages/camera-source.yaml` file entry for every additional
camera. `camera_id` must be unique in that device and valid in ESPHome IDs
(use lower-case letters, numbers, and underscores).

For a local trial, copy this project directory beside your private device YAML.
Include the hardware/camera profile plus one or more local
`packages/camera-source.yaml` template instances with `vars`. See the examples
for the exact pattern. Do not use local and remote forms at once. A public GitHub token is not needed for
an ESPHome builder to read a public repository. Firmware binaries containing
real credentials must stay private.

## Hardware profiles

| File | Hardware and memory | Camera code |
| --- | --- | --- |
| `profiles/esp32-c3.yaml` | C3, 160 MHz, no PSRAM; 8-bit / 50% buffer; lighter 4-direction battery keyline | Omitted |
| `profiles/esp32-c3-camera.yaml` | Same C3 settings | Included |
| `profiles/esp32-s3-quad-psram.yaml` | S3, 240 MHz, 4 MB flash, confirmed quad PSRAM at 80 MHz; 16-bit / full buffer; full 8-direction battery keyline | Omitted |
| `profiles/esp32-s3-quad-psram-camera.yaml` | Same S3 quad-PSRAM settings | Included |
| `profiles/esp32-c3-templated.yaml` | C3 template-driven arbitrary page registry | Omitted |
| `profiles/esp32-c3-templated-camera.yaml` | C3 template registry + camera alerts/pages | Included |
| `profiles/esp32-s3-quad-psram-templated.yaml` | S3 template-driven arbitrary page registry | Omitted |
| `profiles/esp32-s3-quad-psram-templated-camera.yaml` | S3 template registry + camera alerts/pages | Included |

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

The original numbered `metric_1..metric_6` settings remain supported by the
legacy profiles so existing deployments do not change unexpectedly.

For new builds, the **templated** profiles use repeatable package instances:
`rotation-numeric-page.yaml`, `rotation-battery-page.yaml`, and optionally
`rotation-camera-page.yaml`. Each instance supplies its own `page_id`,
`page_order`, duration, entity, and display settings. Adding a seventh or
tenth numeric page does not require changing shared source code.

The configured unit is metadata, not unit conversion. Home Assistant must supply
values in the intended units.

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

Version 0.5.0 remains a hardware-validation candidate, not
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
