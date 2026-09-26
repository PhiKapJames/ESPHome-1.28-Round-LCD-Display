# Local configuration reference

All settings below are `substitutions` unless stated otherwise. Real values go
in your local device/site YAML, outside this repository. `api`, `ota`, and
`wifi` blocks stay local and reference your existing `!secret` keys. The shared
packages deliberately contain no `!secret` lookups.

## Package architecture

Use this project through ESPHome's `packages:` feature. It is not an
`external_components:` repository: there is no custom ESPHome component
implementation to load. The public repository owns reusable YAML renderers and
shared profiles; the private device YAML owns the concrete page/camera instances
and their Home Assistant entity mappings.

Remote package `files:` entries may intentionally reference the same template
more than once with different `vars`. This is the supported mechanism used by
the page and camera-source templates below.

## Identity and rendering

| Setting | Default | Notes |
| --- | --- | --- |
| `device_name` | `round-minion` | Set a unique name; preserve it across firmware updates. |
| `friendly_name` | `Round Minion` | User-facing device name. |
| `timezone` | `Etc/UTC` | Device timezone. |
| `clock_page_duration_ms` | `'8000'` | Clock interstitial duration after every content page. |
| `clock_face_style` | `original` | Clock renderer: `original`, `classic_analog`, `modern_dashboard`, `fitness_ring`, or `clean_arc`. |

## Clock face styles

The clock is still a single shared interstitial page, but its renderer is
selectable per device with one substitution:

```yaml
substitutions:
  clock_face_style: modern_dashboard
```

Available values:

- `original` — the established nested cyan/blue/purple digital face; this remains the default.
- `classic_analog` — traditional 12/3/6/9 dial, cyan tick marks, white hour/minute hands, and a red seconds hand.
- `modern_dashboard` — large digital time, date, colored perimeter markers, and asymmetric status motifs.
- `fitness_ring` — large digital time with a bold minute-progress outer ring.
- `clean_arc` — centered digital time with cyan/red side arcs and a compact progress bar.

The additional faces intentionally require no weather, battery, or other Home
Assistant entities. This keeps clock selection independent of each site's
available sensors. A later optional-data layer can enrich individual faces
without changing the base selector.

An unknown value displays a visible `CLOCK STYLE / UNKNOWN` diagnostic on the
device so configuration mistakes are obvious.

## Rotation page templates

Version 0.5.0 removes the six-page limit from the rotation engine. The display
maintains an ordered registry populated by page-template instances at boot.
Each template has a unique `page_id`, integer `page_order`, and
`page_duration_ms`. The clock is still inserted automatically after every
normal content page.

### Numeric / temperature page

Include `packages/page-numeric.yaml` once for every numeric page. There is no
shared-code count limit.

```yaml
- path: packages/page-numeric.yaml
  vars:
    page_id: kitchen
    page_label: Kitchen
    page_entity: sensor.kitchen_temperature
    page_duration_ms: '4000'
    page_order: '10'
    page_unit: °F
    page_suffix: °
    page_decimals: '1'
    page_panel_style: '1'
    page_color_red: 0%
    page_color_green: 62%
    page_color_blue: 45%
```

`page_unit` is Home Assistant sensor metadata and does not convert values.
`page_suffix` is the text rendered after the number. Colors are independent
per page.

Numeric and battery pages do not render history/trend graphs. No graph interval
or graph-color variables are required in local device YAMLs.

### Battery page

Include `packages/page-battery.yaml` for each battery percentage page:

```yaml
- path: packages/page-battery.yaml
  vars:
    page_id: main_battery
    page_label: Battery
    page_entity: sensor.main_battery_percent
    page_duration_ms: '4000'
    page_order: '50'
```

The battery renderer keeps the 0–25 red, 25–50 yellow, 50–75 cyan/blue, and
75–100 green bands. Multiple battery pages are allowed.

### Camera rotation page

`packages/page-camera.yaml` deliberately puts a still camera view into normal
rotation. It is optional and separate from alert snapshots. It requires a
camera-enabled profile because it reuses that profile's shared HTTP requester.

```yaml
- path: packages/page-camera.yaml
  vars:
    page_id: driveway_view
    page_label: DRIVEWAY
    page_entity: camera.driveway
    page_duration_ms: '5000'
    page_order: '60'
```

The page requests the camera's current `entity_picture` when it enters
rotation, releases the decoded image when it leaves, and uses the same
origin/token validation and RAM guards as the alert design. Adding a camera
rotation page does **not** change camera-alert trigger rules.

Practical limits remain the device's RAM, flash, component count, and Home
Assistant subscriptions rather than an artificial page-count constant. CI
includes a synthetic 12-content-page configuration containing 10 numeric pages,
one battery page, and one camera page.

Numeric and battery pages show a sliding page-position indicator. Up to nine
page dots are displayed at once. When earlier pages are outside the visible
window a left chevron is shown; when later pages are outside the visible window
a right chevron is shown. The active page stays centered when possible. Camera
rotation pages remain clean full-screen images and do not overlay the indicator.

## Hardware overrides

| Setting | Default |
| --- | --- |
| `spi_clk_pin` | `GPIO1` |
| `spi_mosi_pin` | `GPIO2` |
| `display_cs_pin` | `GPIO5` |
| `display_dc_pin` | `GPIO4` |
| `display_reset_pin` | `GPIO9` |
| `backlight_pin` | `GPIO6` |
| `backlight_restore_mode` | `ALWAYS_ON` |
| `display_rotation_degrees` | `'0'` |
| `display_spi_rate` | `80MHz` |
| `battery_outline_quality` | hardware profile | `1` = four-direction C3/C6 keyline; `2` = full eight-direction S3 keyline. |

`display_color_depth`, `display_buffer_size`, and `battery_outline_quality` are supplied by the selected
hardware profile.

For the C6 profile, the public reference pin map is GPIO18 clock, GPIO19 MOSI,
GPIO20 CS, GPIO21 DC, GPIO22 reset, and GPIO23 backlight. This is deliberately
separate from the older shared C3/S3 wiring because ESP32-C6 GPIO4/5/8/9/15 are
strapping pins and GPIO12/13 are native USB Serial/JTAG. Override the C6 pins in
the private device YAML if the actual PCB uses another map.

Do not copy the S3/full-buffer choice onto a C3 or C6 to silence warnings. Actual free contiguous memory matters for camera allocations.
Backlight is a manual/HA output switch. Its default restore behavior is
`ALWAYS_ON`, controlled by the `backlight_restore_mode` substitution. Devices
with strict schedules can override it locally, for example
`backlight_restore_mode: ALWAYS_OFF`, without changing the shared default.
The `LCD Backlight` switch is also the shared display-enabled gate. When it is
OFF, normal page rotation stops, no display redraws are requested, camera alert
requests are ignored, active alert refresh/download state is released, and an
optional normal-rotation camera page cleans up its image. Home Assistant entity
subscriptions, Wi-Fi, time, and other non-display services remain active.

Turning `LCD Backlight` ON starts a clean normal rotation from the first
configured content page. The shared code does not decide *why* the switch is
turned on or off: schedules and Home Assistant automations can both control the
same switch. Quiet-hours automation is not added automatically; existing
per-device schedules can remain local.

The shared display clock uses ESPHome's **Home Assistant time** platform with
the internal ID `ha_time`; it is not SNTP. Device-specific schedules that must
continue before or without a Home Assistant connection may add a separate SNTP
time source in the private device YAML.

## Optional camera feature

A `*-camera.yaml` profile adds the shared camera engine: HTTP/JPEG download,
full-screen rendering, timeout/RAM guards, and the alert queue. The engine uses
two decoded-image slots when optional periodic refresh is enabled so the current
good frame can remain visible while the next frame downloads. Only one JPEG is
downloaded/decoded at a time. Camera sources are separate instances of
`packages/camera-source.yaml`.

There is **no hard-coded camera count**. ESPHome remote packages allow the same
file to be listed repeatedly with different `vars`; each instance contributes
one HA camera attribute subscription, one manual button, one per-source cooldown,
one per-camera **Alerts** configuration switch, and whichever detector subscriptions are enabled. Practical flash/RAM/API entity
limits still apply, but adding a fifth, sixth, or later camera does not require
editing this repository.

A source works with any HA `camera.*` entity. A one-lens camera needs no special
handling. For a multi-lens camera, choose the particular lens entity you want
shown.

Shared engine substitutions:

| Setting | Default | Meaning |
| --- | --- | --- |
| `ha_base_url` | `http://homeassistant.local:8123` | HA origin reachable by the device; same HA that supplies camera attributes. |
| `camera_image_width` | `'200'` | Maximum decoded source width. |
| `camera_image_height` | `'112'` | Maximum decoded source height; the renderer center-crops to fill 240×240. |
| `camera_hold_time` | `15s` | Fixed display time for a successful **manual** snapshot request. |
| `camera_min_hold_time` | `7s` | Minimum display time for a successful automatic person/vehicle alert. |
| `camera_clear_delay` | `2s` | After the minimum, all enabled detectors for that camera must remain continuously OFF for this long before rotation resumes. |
| `camera_max_hold_ms` | `'30000'` | Hard maximum for a successful automatic alert's hold/follow phase, measured from the first successful image. `0` disables the hard cap. A camera-source file entry can override this value for that source. |
| `camera_refresh_interval_ms` | `'0'` | Optional alert-image refresh interval in milliseconds; `0` keeps the established single-snapshot behavior. A value such as `'1000'` requests a new still about once per second, never overlapping downloads. |
| `camera_download_timeout` | `20s` | Whole-download cooperative backstop. |
| `camera_error_hold_time` | `4s` | Failure-screen duration. |
| `camera_queue_expire_ms` | `'60000'` | Drop stale automatic requests that waited this long. |
| `camera_queue_max_runs` | `'20'` | Maximum active+queued alert operations; this limits backlog, **not camera count**. |
| `camera_min_free_heap` | `'100000'` | Preflight free-heap threshold. |
| `camera_min_largest_block` | `'60000'` | Preflight largest-contiguous-block threshold. |

When `camera_refresh_interval_ms` is greater than zero, the alert renderer uses
a ping-pong pair of image slots. The last successfully decoded frame remains on
screen while the inactive slot downloads the next JPEG. A failed or timed-out
refresh keeps the last good frame visible.

Automatic person/vehicle alerts are detector-driven. They remain visible for at
least `camera_min_hold_time`, continue while any enabled detector for that
camera is ON, then require every enabled detector to remain continuously OFF for
`camera_clear_delay`. If a detector turns back ON during the clear delay, that
delay is cancelled and restarts after the next clear transition.

A successful automatic alert is also bounded by `camera_max_hold_ms`, measured
from the first successfully decoded image. The default is 30 seconds. The hard
maximum wins even if a detector is still ON or the clear-delay tail has not
completed. Set it to `0` to disable the cap. A camera can override the shared
value by supplying `camera_max_hold_ms` in that camera-source entry's `vars`.

Manual snapshot requests do not follow detector state and retain the fixed
`camera_hold_time`. The display-off gate still cancels either kind of alert
immediately.

Each `packages/camera-source.yaml` instance requires these variables:

| Variable | Example | Meaning |
| --- | --- | --- |
| `camera_id` | `driveway` | Unique ESPHome-ID-safe source key; use lower-case letters/numbers/underscores. |
| `camera_entity` | `camera.driveway` | Exact HA camera whose `entity_picture` is requested. |
| `camera_source_label` | `DRIVEWAY` | Loading/error footer; keep to supported uppercase glyphs. |
| `camera_status_label` | `driveway` | Human-readable status/log label. |
| `camera_button_name` | `Show Driveway Snapshot` | HA manual/automation override button. |
| `camera_trigger_person` | `'true'` | Include a person detector subscription. |
| `camera_person_entity` | `binary_sensor.driveway_person` | Person entity; supply a valid placeholder even if the trigger is false. |
| `camera_trigger_vehicle` | `'true'` | Include a vehicle detector subscription. |
| `camera_vehicle_entity` | `binary_sensor.driveway_vehicle` | Vehicle entity; supply a valid placeholder even if the trigger is false. |
| `camera_cooldown_ms` | `'60000'` | Automatic cooldown for only this source. |
| `camera_max_hold_ms` | omitted | Optional per-source override of the shared `camera_max_hold_ms`. Example: `'45000'` for 45 seconds, or `'0'` for no hard cap. |

When person and vehicle are both enabled on one source, they are **OR** triggers
both for starting the alert and for keeping it visible: the alert remains active
until both detectors are OFF and the configured clear delay has elapsed.
A vehicle-only source does not subscribe to its person entity. A manual-only
source sets both trigger flags false but still gets its snapshot button.

Every source exposes its own **<SOURCE> Alerts** switch, so automatic alerts are
enabled or disabled independently per camera. Manual snapshot buttons bypass
that source's automatic-alert switch and cooldown, but retain the readiness/RAM
safeguards.

The user-facing diagnostic is **Last Camera Alert**. It remains short, for
example `FRONT: Person` or `DRIVEWAY: Vehicle`. Manual snapshots do not
replace it. Internal download/progress status is no longer exposed as a separate
Home Assistant diagnostic entity.

Example remote package with two cameras:

```yaml
packages:
  round_minion:
    url: https://github.com/PhiKapJames/ESPHome-1.28-Round-LCD-Display
    ref: <tested-commit-sha>
    files:
      - profiles/esp32-c3-camera.yaml

      - path: packages/camera-source.yaml
        vars:
          camera_id: driveway
          camera_entity: camera.driveway
          camera_source_label: DRIVEWAY
          camera_status_label: driveway
          camera_button_name: Show Driveway Snapshot
          camera_trigger_person: 'true'
          camera_person_entity: binary_sensor.driveway_person
          camera_trigger_vehicle: 'true'
          camera_vehicle_entity: binary_sensor.driveway_vehicle
          camera_cooldown_ms: '60000'
          # Optional: override the shared 30-second maximum for this camera.
          camera_max_hold_ms: '45000'

      - path: packages/camera-source.yaml
        vars:
          camera_id: parking
          camera_entity: camera.parking
          camera_source_label: PARKING
          camera_status_label: parking
          camera_button_name: Show Parking Snapshot
          camera_trigger_person: 'false'
          camera_person_entity: binary_sensor.parking_person
          camera_trigger_vehicle: 'true'
          camera_vehicle_entity: binary_sensor.parking_vehicle
          camera_cooldown_ms: '60000'
    refresh: 1d
```

Only **one alert JPEG is decoded at a time**, regardless of how many camera
sources are configured. Source requests enter a bounded shared queue containing
strings and small parameters, not images. Per-source cooldowns suppress duplicate
automatic detections before queueing; stale automatic requests expire so a burst
cannot monopolize the display indefinitely. Manual requests bypass the source
Alerts switch and cooldown but use the same alert engine.

The original RAM thresholds are conservative checks, not guarantees of decoder
success. Camera access tokens come from each source's current `entity_picture`,
are accepted only for the configured HA origin and exact camera proxy path, and
are removed from the downloader URL after each request.

The image request is HTTP/HTTPS separate from the native encrypted ESPHome API.
An HTTP origin is unencrypted on the LAN. HTTPS requires a trusted certificate;
`verify_ssl: true` remains enabled.

## Multiple Home Assistant instances

The ESPHome builder's location does not select the source HA. Pair the device
with the intended HA instance and use that instance's entity mappings and
camera origin. Site configuration can be a local `packages` include reused by
many devices; root/device values take precedence over inherited packages.
Credentials stay in the local ESPHome `secrets.yaml`. Avoid connecting a minion
to both Home and another HA that publish colliding entity IDs unless you have a
separate deliberate routing design.


## Renderer performance notes

Version 0.4.0 precomputes the static metric and clock arc coordinates and the
60 minute-marker positions. This removes runtime sine/cosine calculations from
normal metric/clock drawing without changing those coordinates.

Version 0.6.8 reduces repeated framebuffer writes on page transitions without
lowering the configured display color depth, buffer size, or SPI rate:

- rounded metric/battery panels use one horizontal span per scanline instead of
  overlapping two filled rectangles and four filled circles;
- repeated radius-2/radius-3 arc markers use non-overlapping scanline shapes
  instead of `filled_circle()`'s duplicate border/span writes;
- the S3/high-quality battery percentage keyline uses one bold black underlay
  plus the regular white value instead of eight offset renders of the 84 px font;
- the original clock face clears only the ring pixels that cross behind its
  large hour/minute text instead of repainting large black rectangles.

The display still refreshes on each normal page transition. The previous extra
full redraw at every minute boundary was removed because normal pages already
rotate every few seconds; Home Assistant time synchronization can still request
a refresh when time first becomes valid.

C3 and the 4 MB/no-PSRAM C6 profile keep the 50% framebuffer to preserve
camera RAM headroom and use the established four-direction battery percentage
keyline. S3 quad-PSRAM keeps its 100% framebuffer and uses the optimized bold
underlay keyline. This is an intentional hardware-performance difference, not a
layout/theme change.
