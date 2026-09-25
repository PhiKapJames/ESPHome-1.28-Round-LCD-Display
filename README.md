# HA ESP Round Minions

Reusable ESPHome packages for 240 × 240 GC9A01A round displays connected to
Home Assistant. Keep shared display code here; keep actual device names,
entity mappings, Home Assistant origins, Wi-Fi credentials, API keys, and OTA
passwords in local ESPHome configuration files.

**Version: 0.6.4 — detector-following camera alert lifetime.** GitHub Actions validates and
compiles the synthetic ESPHome profile matrix for repository changes. Validate
your private device configuration and test one physical device before broad
rollout. See [validation](docs/VALIDATION.md).

## What it displays

- Any number of reusable numeric/temperature and battery-percentage rotation
  pages, ordered with `page_order`.
- Large centered readings, rounded panels, location accents, and a sliding
  page-position indicator. Trend/history graphs are intentionally omitted. Up to nine dots are shown at once;
  left/right chevrons indicate additional pages before or after the visible window.
- A shared clock between each enabled content page, with selectable `original`, `classic_analog`, `modern_dashboard`, `fitness_ring`, and `clean_arc` renderers.
- A horizontal battery silhouette filled from the reported percentage, with
  red/yellow/cyan/green charge bands and a high-contrast outlined value.
- Optional detection-only camera snapshots from reusable camera-source package
  instances. There is no hard-coded camera count: add another instance in the
  device's private package list. Each source can trigger on person, vehicle,
  both (OR), or neither/manual-only. Single-lens and multi-lens cameras are
  treated the same; configure the HA camera entity whose image you want.
  Alert snapshots never join the regular playlist unless a separate
  `page-camera.yaml` rotation-page template is explicitly configured.
  Optional periodic refresh can request successive stills during an alert while
  keeping the last good frame visible if a refresh fails. Automatic person/vehicle
  alerts can remain visible while any enabled detector for that camera is active,
  then stay visible for a configurable clear delay after all detectors turn off.
- An optional normal-rotation camera-page template for deliberately putting a
  camera view into the playlist.
- A manual/automation snapshot button and independent Alerts switch for every
  configured camera source.
  Overrides bypass automatic enable/cooldown, not readiness or RAM checks.
- Alerts save the current page and its remaining duration, then resume afterward.
- The `LCD Backlight` switch is the shared display-enabled gate: when OFF,
  rotation/redraws stop and camera requests are ignored/released while Wi-Fi,
  Home Assistant, time, and other non-display services remain connected.

Version 0.5.0 replaces the fixed six-slot scheduler with one ordered runtime
page registry. Pages are explicit template instances: `page-numeric.yaml`,
`page-battery.yaml`, and optionally `page-camera.yaml`. There is no fixed
numeric/battery page count in shared code; practical hardware resources are the
limit.

## Installation

Requires **ESPHome 2026.9.0 or newer**. The initial CI image is pinned to
`ghcr.io/esphome/esphome:2026.9.0`. Newer builders should be tested before updating
all devices. Packages are downloaded by the builder at build time; devices do
not pull YAML from GitHub and do not update merely because this repo changes.

### ESPHome package architecture

This repository intentionally uses ESPHome **`packages:`**, not
**`external_components:`**. `external_components` is for custom ESPHome
component implementations (Python/C++ component code). This project distributes
reusable YAML configuration and template instances, so remote packages are the
appropriate mechanism.

The explicit `files:` entries in a private device YAML are also intentional.
ESPHome's remote-package format supports loading the same template file multiple
times with different `vars`. That is how each device creates its own numeric,
battery, camera-page, and camera-source instances while keeping private Home
Assistant entity IDs out of this public repository. The selected profile then
uses relative `!include` files internally for shared hardware, core, theme,
clock, and optional camera-engine configuration.

For active development, `ref: main` with a reasonable `refresh` interval is
convenient. For deployed devices, prefer a tested immutable commit SHA or release
tag; a pinned source can use `refresh: never` to avoid unnecessary update
checks.

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
    url: https://github.com/PhiKapJames/ESPHome-1.28-Round-LCD-Display
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
| `profiles/esp32-c6.yaml` | C6, 160 MHz, 4 MB flash, no PSRAM; 8-bit / 50% buffer; native USB logging; C6-safe reference GC9A01 pins | Omitted |
| `profiles/esp32-c6-camera.yaml` | Same C6 settings | Included |
| `profiles/esp32-s3-quad-psram.yaml` | S3, 240 MHz, 4 MB flash, confirmed quad PSRAM at 80 MHz; 16-bit / full buffer; full 8-direction battery keyline | Omitted |
| `profiles/esp32-s3-quad-psram-camera.yaml` | Same S3 quad-PSRAM settings | Included |

The S3 profiles are **not** for every S3 module. Confirm flash capacity, PSRAM
presence, mode, pin assignments, and wiring. Do not select the S3 PSRAM profile
for a C3/C6 or an S3 without the stated memory.

The C6 profile targets the reported ESP32-C6 revision-2 class with 4 MB flash,
using `esp32-c6-devkitc-1`, explicit `variant: esp32c6`, ESP-IDF, and native
USB Serial/JTAG logging. Silicon revision is runtime-detected rather than selected
in YAML; the 40 MHz crystal also needs no project override. No PSRAM is configured
for this profile. Its reference GC9A01A map uses GPIO18–GPIO23 so it
does not consume the C6 strapping pins (GPIO4/5/8/9/15), native USB pins
(GPIO12/13), UART0 pins (GPIO16/17), or flash-reserved GPIO24–GPIO30. Override
those display pins locally when the physical board is wired differently.

ESP32-C6 also provides Wi-Fi 6, Bluetooth 5 LE, and IEEE 802.15.4 hardware.
Round Minions only enables the Wi-Fi path; it does not automatically enable
Bluetooth, Thread, or Zigbee components. The current backlight is a plain GPIO
output, so the C6 single LEDC group / six PWM channels are not consumed by it. Silicon revision, flash-encryption,
secure-boot, and JTAG eFuse state are detected/provisioned by the hardware and
are not changed by this repository. Device MAC addresses are intentionally
never stored here.

The default LCD SPI rate is 80 MHz, preserving the established device setting.
If the display corrupts, override `display_spi_rate: 40MHz` locally. PSRAM speed
and LCD SPI speed are separate settings. Never hide timing warnings as a fix.

## Clock faces

The clock page is shared by every hardware profile and appears between normal
rotation pages. Its appearance is selected per device with the
`clock_face_style` substitution in the private device YAML.

The established clock remains the default, so existing devices keep their
current appearance unless a different style is explicitly selected.

| `clock_face_style` | Description |
| --- | --- |
| `original` | Established stacked digital face with cyan/blue rings, purple orbit accents, and a moving minute marker. |
| `classic_analog` | Traditional analog dial with 12/3/6/9 numerals, minute ticks, white hour/minute hands, and a red seconds hand. |
| `modern_dashboard` | Large digital time with date, AM/PM, colored perimeter markers, and asymmetric smartwatch-style status accents. |
| `fitness_ring` | Large digital time with a bold outer minute-progress ring and compact date/status details. |
| `clean_arc` | Minimal centered digital time with cyan/red side arcs, date, AM/PM, and a small minute-progress bar. |

### Selecting a clock face

Add `clock_face_style` to the top-level `substitutions:` block in the private
device YAML:

```yaml
substitutions:
  device_name: camper-minion-1
  friendly_name: Camper Minion 1
  timezone: America/New_York

  clock_page_duration_ms: "8000"
  clock_face_style: modern_dashboard
```

Do **not** place `clock_face_style` inside the remote `packages:` block or
inside an individual page template.

To return to the established face:

```yaml
clock_face_style: original
```

Changing the clock face is a build-time configuration change. Run ESPHome
**Validate**, then compile and install the firmware again. It is not currently a
runtime Home Assistant selector.

The built-in clock faces require no additional Home Assistant weather, battery,
temperature, or humidity entities. They use the Home Assistant time source
already provided by the shared package.

If a newly merged package change is not being picked up while testing with
`ref: main`, remember that the remote package may be cached according to its
`refresh` setting. A configuration using `refresh: 1d` can keep the previous
remote package for up to a day. During active testing, `refresh: 0s` can be used
temporarily to force a remote check on each validation/build; restore the normal
refresh interval afterward.

An invalid style value renders a visible `CLOCK STYLE / UNKNOWN` diagnostic
instead of silently falling back to another face.

## Configuration

See [configuration reference](docs/CONFIGURATION.md). Site settings can be shared
with a local package such as `!include minion-sites/site.yaml`. These local site
files and `secrets.yaml` must **not** be uploaded to this repository.

Rotation content is defined entirely by template instances. Each page supplies
its own `page_id`, `page_order`, duration, source entity, and renderer-specific
settings. Configurations such as 10 temperature pages + 1 battery page are
ordinary configuration changes rather than shared-code changes. See
[configuration reference](docs/CONFIGURATION.md) and
[template example](examples/template-pages.example.yaml).

The configured numeric-page `page_unit` is metadata, not unit conversion.
Home Assistant must supply values in the intended units.

Camera snapshots use the camera entity's `entity_picture` attribute and its
rotating token. Set `ha_base_url` to the same Home Assistant instance importing
that attribute. By default each accepted trigger requests one still. Setting
`camera_refresh_interval_ms` above zero requests successive stills serially
during the alert window. Automatic detector alerts show for at least
`camera_min_hold_time`, continue while any enabled person/vehicle detector for
that camera remains active, and end only after all enabled detectors stay clear
for `camera_clear_delay`. Manual snapshot buttons continue to use the fixed
`camera_hold_time`. This is still not a live stream and a still is not
necessarily the exact frame that caused detection. Only the expected camera
proxy path and configured origin are accepted. Token-bearing URLs are not logged
by the project's own logs, and potentially URL-bearing component logs are muted.
Do not enable verbose logging and publish it without redaction.

An HTTP origin means unencrypted image traffic on the LAN. HTTPS requires a
trusted certificate; `verify_ssl: true` is preserved. No administrator token or
camera username/password belongs in this public repository. The native ESPHome
API's encryption does not encrypt the separate HTTP request.

## Repository maintenance

`packages/` holds the shared scheduler, renderers, and camera code.
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

Version 0.6.4 is validated by the repository's synthetic ESPHome CI matrix but
is not, by itself, a claim that every hardware/profile combination has been
physically validated. Check the Actions results for the exact commit
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
