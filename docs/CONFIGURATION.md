# Local configuration reference

All settings below are `substitutions` unless stated otherwise. Real values go
in your local device/site YAML, outside this repository. `api`, `ota`, and
`wifi` blocks stay local and reference your existing `!secret` keys. The shared
packages deliberately contain no `!secret` lookups.

## Identity and rendering

| Setting | Default | Notes |
| --- | --- | --- |
| `device_name` | `round-minion` | Set a unique name; preserve existing names when migrating. |
| `friendly_name` | `Round Minion` | User-facing device name. |
| `timezone` | `Etc/UTC` | Your timezone; not inferred from the builder's location. |
| `graph_interval` | `12h` | Graph history. |
| `clock_page_duration_ms` | `'8000'` | Milliseconds, positive integer string. |
| `metric_panel_style` | `'1'` | 0 none / 1 rounded panel / 2 horizontal band. Battery always uses its own body. |
| `metric_N_enabled` | `'true'` | N=1–6. Use `'true'` or `'false'`. Must leave at least one enabled. |
| `metric_N_label` | `Metric N`, slot 6 `Battery` | Keep short enough for 44px type. No embedded quotes, backslashes, or newlines. |
| `metric_N_entity` | `sensor.example_metric_N` | Real HA entity of a numeric sensor; ignored for a disabled slot. |
| `metric_N_duration_ms` | `'8000'` | Positive integer milliseconds for each content page. |
| `metric_N_unit` | `°F` | N=1–5; metadata, **not conversion**. |
| `metric_N_suffix` | `°` | N=1–5; text after displayed number. |
| `metric_N_decimals` | `'1'` | N=1–5; decimals in the number. Slot 6 displays whole percent. |

For example, no battery on a display:

```yaml
substitutions:
  metric_6_enabled: 'false'
```

The 84px value stays centered. Values wider than 220 pixels can lose the decimal
rather than shrinking the font. Other very long numeric values/suffixes are not
arbitrarily auto-fit. The current geometry is for temperatures and battery
percentages, not long text. Font families/sizes remain 44px Roboto title, 84px
Roboto value, 36px Roboto footer, 92px Oswald hour/minute.

## Hardware overrides

| Setting | Default |
| --- | --- |
| `spi_clk_pin` | `GPIO1` |
| `spi_mosi_pin` | `GPIO2` |
| `display_cs_pin` | `GPIO5` |
| `display_dc_pin` | `GPIO4` |
| `display_reset_pin` | `GPIO9` |
| `backlight_pin` | `GPIO6` |
| `display_rotation_degrees` | `'0'` |
| `display_spi_rate` | `80MHz` |
| `battery_outline_quality` | hardware profile | `1` = four-direction C3 keyline; `2` = full eight-direction S3 keyline. |

`display_color_depth`, `display_buffer_size`, and `battery_outline_quality` are supplied by the selected
hardware profile. Do not copy the S3/full-buffer choice onto a C3 to silence
warnings. Actual free contiguous memory matters for camera allocations.
Backlight is a manual/HA output switch with `ALWAYS_ON` restore behavior in
v0.4.0. Quiet-hours automation is not added automatically. Existing per-device
quiet-hours logic can be kept in a local package when migrating other minions.

## Optional camera feature

A `*-camera.yaml` profile adds the **shared camera engine only**: HTTP/JPEG
download, the single decoded image buffer, full-screen rendering, Camera Alerts
switch, timeout/RAM guards, and the alert queue. Camera sources are separate
instances of `packages/camera-source.yaml`.

There is **no hard-coded camera count**. ESPHome remote packages allow the same
file to be listed repeatedly with different `vars`; each instance contributes
one HA camera attribute subscription, one manual button, one per-source cooldown,
and whichever detector subscriptions are enabled. Practical flash/RAM/API entity
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
| `camera_hold_time` | `15s` | Display time after a successful decode. |
| `camera_download_timeout` | `20s` | Whole-download cooperative backstop. |
| `camera_error_hold_time` | `4s` | Failure-screen duration. |
| `camera_queue_expire_ms` | `'60000'` | Drop stale automatic requests that waited this long. |
| `camera_queue_max_runs` | `'20'` | Maximum active+queued alert operations; this limits backlog, **not camera count**. |
| `camera_min_free_heap` | `'100000'` | Preflight free-heap threshold. |
| `camera_min_largest_block` | `'60000'` | Preflight largest-contiguous-block threshold. |

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

When person and vehicle are both enabled on one source, they are **OR** triggers.
A vehicle-only source does not subscribe to its person entity. A manual-only
source sets both trigger flags false but still gets its snapshot button.

Example remote package with two cameras:

```yaml
packages:
  round_minion:
    url: https://github.com/PhiKapJames/HaEspRoundMinions
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

Only **one JPEG is decoded at a time**, regardless of how many source instances
are configured. Source requests enter a bounded shared queue containing strings
and small parameters, not images. Per-source cooldowns suppress duplicate
automatic detections before queueing; stale automatic requests expire so a burst
cannot monopolize the display indefinitely. Manual requests bypass the automatic
Camera Alerts switch and source cooldown but use the same single-buffer engine.

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

The display still refreshes on each normal page transition. The previous extra
full redraw at every minute boundary was removed because normal pages already
rotate every few seconds; Home Assistant time synchronization can still request
a refresh when time first becomes valid.

C3 keeps the 50% framebuffer to preserve camera RAM headroom and uses the
four-direction battery percentage keyline. S3 quad-PSRAM keeps its 100%
framebuffer and full eight-direction keyline. This is an intentional
hardware-performance difference, not a layout/theme difference.
