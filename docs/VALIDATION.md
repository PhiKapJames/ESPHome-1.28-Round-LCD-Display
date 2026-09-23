# Validation status at source preparation

- YAML parsed with duplicate-key detection.
- Offline package/include/substitution expansion checked for five fixtures.
- Component references, graph schemas, and optional camera/PSRAM boundaries checked.
- All 63 nonempty combinations of six enabled slots exercised in structural tests.
- Native C++ selection/resumption tests passed for all 63 nonempty slot masks
  using lightweight stand-ins for the display (not an ESPHome firmware build).
- The empty playlist is rejected by a C++ static assertion.
- Renderer and private-mapping regression checks performed separately from public fixtures.
- Source privacy scan completed before publication.
- **ESPHome configuration validation/firmware compilation has NOT run here.**
  Check the GitHub Actions result for the exact commit; the offline checks below
  are not a successful firmware build result.
- **No physical device has been flashed with these packages.**

`python scripts/check_project.py` is an independent structural test, not ESPHome's
own package resolver or schema validator. It must not be described as a compiler.
The workflow in `.github/workflows/validate.yaml` runs the real commands after
publication, with only synthetic configurations and no secrets from a deployment.

To run the same real build locally with Docker, from the repository root:

```sh
docker run --rm -v "$PWD":/config ghcr.io/esphome/esphome:2026.9.0 \
  config tests/esp32-c3-camera.yaml

docker run --rm -v "$PWD":/config ghcr.io/esphome/esphome:2026.9.0 \
  compile tests/esp32-c3-camera.yaml

docker run --rm -v "$PWD":/config ghcr.io/esphome/esphome:2026.9.0 \
  config tests/esp32-c6-camera.yaml

docker run --rm -v "$PWD":/config ghcr.io/esphome/esphome:2026.9.0 \
  compile tests/esp32-c6-camera.yaml
```

Those tests generate synthetic firmware. **Do not install the test fixture on
an existing device**: it intentionally has fake Wi-Fi/API/OTA credentials.
Validate and compile the private local device YAML separately for deployment.

A first physical migration should verify that the identity and HA controls are
unchanged, all six existing screens retain their geometry, person detection and
the snapshot override display the full-screen crop, failure paths return to the
playlist, and RAM recovers after repeated alerts. Test an S3 separately before
applying the S3 profile to additional devices.


## ESP32-C6 profile

CI validates and compiles both the base and camera-enabled ESP32-C6 synthetic
fixtures. The profile targets 4 MB flash, no PSRAM, ESP-IDF, and native
USB Serial/JTAG logging. A successful synthetic compile proves configuration and
toolchain compatibility only; it does not claim a particular C6 board/display
wiring has been physically validated.
