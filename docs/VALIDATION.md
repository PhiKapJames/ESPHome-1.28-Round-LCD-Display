# Validation

The repository uses two complementary validation layers:

- `scripts/check_public.py` checks the public source for privacy/safety invariants.
- `scripts/check_project.py` performs offline structural package, substitution,
  renderer, camera-routing, backlight-gating, and regression checks.
- `.github/workflows/validate.yaml` runs the real ESPHome toolchain on every
  pull request and push to `main`.
- The Actions matrix currently covers 10 synthetic configurations across ESP32-C3,
  ESP32-C6, and ESP32-S3, including base, camera, multi-camera, migration, and
  template-page fixtures.
- Every matrix job runs both `esphome config` and `esphome compile` using
  `ghcr.io/esphome/esphome:2026.9.0`.
- The synthetic fixtures contain no deployment secrets and are never installed
  by CI.

The offline Python checks are intentionally **not** described as a compiler and
do not replace ESPHome validation. Likewise, this document does not claim that
an arbitrary commit is green: check the GitHub Actions result for the exact
commit or pull request you plan to deploy.

ESPHome 2026.9.0 requires Python 3.12+ for a native Python installation. The
official Docker image is the recommended way to reproduce CI without depending
on the host Python version.

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
