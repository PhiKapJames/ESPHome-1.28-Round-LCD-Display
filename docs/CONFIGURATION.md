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

`display_color_depth` and `display_buffer_size` are supplied by the selected
hardware profile. Do not copy the S3/full-buffer choice onto a C3 to silence
warnings. Actual free contiguous memory matters for camera allocations.
Backlight is a manual/HA output switch with `ALWAYS_ON` restore behavior in
v0.1.0. Quiet-hours automation is not added automatically. Existing per-device
quiet-hours logic can be kept in a local package when migrating other minions.

## Optional camera feature

Only a `*-camera.yaml` profile includes HTTP/image decoding, camera-source
subscriptions, status, the global Camera Alerts switch, and manual snapshot
buttons. Basic profiles compile without those components.

The camera engine supports **up to four independent sources** while keeping one
shared downloader/decoded image buffer. A source is a Home Assistant
`camera.*` entity; it does not need to have a particular lens count. For a
dual-lens camera, choose whichever lens camera entity you want. For a
single-lens camera, use its one camera entity directly.

Shared settings:

| Setting | Default | Meaning |
| --- | --- | --- |
| `ha_base_url` | `http://homeassistant.local:8123` | HA origin reachable by the device; same HA that provides camera attributes. |
| `camera_image_width` | `'200'` | Maximum decoded source width; not output-screen width. |
| `camera_image_height` | `'112'` | Maximum decoded source height. Image is center-cropped and scaled for 240×240. |
| `camera_hold_time` | `15s` | Display time after decode succeeds. |
| `camera_download_timeout` | `20s` | Cooperative whole-download backstop. |
| `camera_error_hold_time` | `4s` | Text-only failure screen duration. |
| `camera_min_free_heap` | `'100000'` | Preflight free-heap threshold in bytes. |
| `camera_min_largest_block` | `'60000'` | Preflight contiguous-block threshold in bytes. |

Each source N=1–4 has:

| Setting | Example | Meaning |
| --- | --- | --- |
| `camera_N_enabled` | `'true'` | Include this source, its picture attribute, button, and configured detectors. |
| `camera_N_entity` | `camera.driveway` | Exact camera entity whose `entity_picture` is downloaded. |
| `camera_N_source_label` | `DRIVEWAY` | Loading/error footer. Keep to supported uppercase glyphs. |
| `camera_N_status_label` | `driveway` | Human-readable diagnostic status label. |
| `camera_N_button_name` | `Show Driveway Snapshot` | Manual/HA-automation override control. |
| `camera_N_trigger_person` | `'true'` | Subscribe to the person entity and trigger on new detection. |
| `camera_N_person_entity` | `binary_sensor.driveway_person` | Person detector for this source. Ignored when trigger is false. |
| `camera_N_trigger_vehicle` | `'true'` | Subscribe to the vehicle entity and trigger on new detection. |
| `camera_N_vehicle_entity` | `binary_sensor.driveway_vehicle` | Vehicle detector for this source. Ignored when trigger is false. |
| `camera_N_cooldown_ms` | `'60000'` | Automatic cooldown for this source only, in milliseconds. |

When both person and vehicle are enabled for one source, the rule is **OR**:
either new detection requests that source's snapshot. A vehicle-only camera does
not react to person detections. Different sources have independent cooldowns.

Source 1 keeps compatibility aliases from the original one-camera package:

`camera_entity` → `camera_1_entity`,
`person_entity` → `camera_1_person_entity`,
`camera_source_label` → `camera_1_source_label`, and
`camera_status_label` → `camera_1_status_label`.

That means existing Camper local YAML can remain single-camera while Home can
use the new numbered settings.

Only **one JPEG is decoded at a time**. The camera script uses a bounded queued
mode so overlapping source requests wait rather than allocate multiple image
buffers. Repeated events from the same source are rejected by that source's
cooldown when their queued turn arrives. The full-screen image is still
alert-only and never joins the metric/clock playlist.

Every enabled source gets a manual snapshot button. Source 1 defaults to
**Show Camera Snapshot** to preserve the established Camper control. Manual
requests bypass the automatic Camera Alerts switch and source cooldown, but
still enforce initialization, source validation, single-buffer sequencing,
timeout, and RAM guards.

The original RAM thresholds remain conservative checks, not guarantees of
decoder success. Decoded image memory is released after each alert. Camera
access tokens are obtained from each source's current `entity_picture`
attribute, accepted only for the configured HA origin and exact camera proxy
path, and are not logged by project messages.

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
