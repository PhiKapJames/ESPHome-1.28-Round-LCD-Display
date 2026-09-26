# Validation

The repository uses three complementary validation layers:

1. `scripts/check_public.py` checks the public source for privacy/safety invariants.
2. `scripts/check_project.py` performs offline structural package, substitution,
   renderer, camera-routing, display-profiler, backlight-gating, and regression
   checks.
3. `.github/workflows/validate.yaml` runs the real ESPHome toolchain on every
   pull request and push to `main`.

The Actions matrix currently covers these 10 synthetic configurations:

- `esp32-c3`
- `esp32-c3-camera`
- `esp32-c3-multi-camera`
- `esp32-c3-one-metric`
- `esp32-c6`
- `esp32-c6-camera`
- `esp32-s3-quad-psram`
- `esp32-s3-quad-psram-camera`
- `esp32-s3-home-migration`
- `esp32-s3-template-pages`

Every matrix job runs both `esphome config` and `esphome compile` using
`ghcr.io/esphome/esphome:2026.9.0`. The config step additionally fails if
ESPHome emits `Could not resolve substitution variable`, because that warning can
otherwise coexist with a successful firmware build. The synthetic fixtures
contain no deployment secrets and are never installed by CI.

The offline Python checks are intentionally **not** described as a compiler and
do not replace ESPHome validation. Likewise, this document does not claim that
an arbitrary commit is green: check the GitHub Actions result for the exact
commit or pull request you plan to deploy.

ESPHome 2026.9.0 requires Python 3.12+ for a native Python installation. The
official Docker image is the recommended way to reproduce CI without depending
on the host Python version.

To run the repository's offline checks locally:

```sh
python scripts/check_public.py
python scripts/check_project.py
```

To run the same real ESPHome toolchain used by CI, from the repository root:

```sh
docker run --rm -v "$PWD":/config ghcr.io/esphome/esphome:2026.9.0 \
  config tests/esp32-c3-camera.yaml

docker run --rm -v "$PWD":/config ghcr.io/esphome/esphome:2026.9.0 \
  compile tests/esp32-c3-camera.yaml

docker run --rm -v "$PWD":/config ghcr.io/esphome/esphome:2026.9.0 \
  config tests/esp32-s3-home-migration.yaml

docker run --rm -v "$PWD":/config ghcr.io/esphome/esphome:2026.9.0 \
  compile tests/esp32-s3-home-migration.yaml
```

Use another matrix fixture in the same commands when validating a profile-specific
change. The workflow remains the authoritative list of profiles that CI builds.

Those tests generate synthetic firmware. **Do not install the test fixture on
an existing device**: it intentionally has fake Wi-Fi/API/OTA credentials.
Validate and compile the private local device YAML separately for deployment.

A first physical migration should verify that identity and Home Assistant
controls are unchanged, configured pages retain their geometry, the
`round_minion.display` profiler reports the expected normal-page labels,
person/vehicle detection and manual snapshot overrides behave as intended,
automatic alerts honor minimum/clear/max-hold behavior, failure paths return to
the playlist, display suspension resumes cleanly, and RAM recovers after
repeated camera alerts. Test an S3 separately before applying the S3 profile to
additional devices.


## ESP32-C6 profile

CI validates and compiles both the base and camera-enabled ESP32-C6 synthetic
fixtures. The profile targets 4 MB flash, no PSRAM, ESP-IDF, and native
USB Serial/JTAG logging. A successful synthetic compile proves configuration and
toolchain compatibility only; it does not claim a particular C6 board/display
wiring has been physically validated.
