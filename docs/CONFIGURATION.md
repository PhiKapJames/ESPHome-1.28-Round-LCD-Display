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

Only a `*-camera.yaml` profile includes HTTP/image decoding, the detection
subscription, camera status, enable switch, and override button. Basic profiles
compile without those components. Default values:

| Setting | Default | Meaning |
| --- | --- | --- |
| `ha_base_url` | `http://homeassistant.local:8123` | HA origin reachable by the device; same HA that provides the attribute. |
| `camera_entity` | `camera.example_camera` | Camera entity to read `entity_picture` from. |
| `person_entity` | `binary_sensor.example_person` | New off-to-on transitions trigger an alert. Initial on state is ignored. |
| `camera_source_label` | `CAMERA` | Loading/error footer; use uppercase letters/digits/spaces/slashes. |
| `camera_status_label` | `camera` | Human-readable status prefix. No quotes, slashes requiring escapes, or newlines. |
| `camera_image_width` | `'200'` | Maximum decoded source width; not output-screen width. |
| `camera_image_height` | `'112'` | Maximum decoded source height. Image is center-cropped and scaled for 240×240. |
| `camera_hold_time` | `15s` | Display time **after** decode succeeds. |
| `camera_download_timeout` | `20s` | Cooperative overall backstop; individual HTTP operations can block. |
| `camera_error_hold_time` | `4s` | Text-only failure screen duration. |
| `camera_cooldown` | `60s` | Automatic trigger cooldown after alert completion. |
| `camera_min_free_heap` | `'100000'` | Preflight free-heap threshold in bytes. |
| `camera_min_largest_block` | `'60000'` | Preflight contiguous-block threshold in bytes. |

The original thresholds are retained, not guarantees of decoder success. One
picture is decoded at a time. The decoded image is released after the alert;
some downloader/decoder memory can remain retained by ESPHome. The full-screen
renderer reuses the small source image, not a second full RGB565 image.

**Show Camera Snapshot** calls the same alert path with `override_request: true`.
It bypasses automatic enable/cooldown but still enforces no overlapping alert,
initialization, image source, and RAM checks. It does not claim active person
detection for manual snapshots. HA automations may call `button.press` on the
actual discovered entity ID. No extra HA action-execution permission is needed:
the device is importing state/attributes, not instructing HA to run an action.

## Multiple Home Assistant instances

The ESPHome builder's location does not select the source HA. Pair the device
with the intended HA instance and use that instance's entity mappings and
camera origin. Site configuration can be a local `packages` include reused by
many devices; root/device values take precedence over inherited packages.
Credentials stay in the local ESPHome `secrets.yaml`. Avoid connecting a minion
to both Home and another HA that publish colliding entity IDs unless you have a
separate deliberate routing design.
