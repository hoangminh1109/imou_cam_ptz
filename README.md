# Imou Camera PTZ

[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

**Imou Camera PTZ** (`imou_cam_ptz`) is a custom integration for Home Assistant. 

 This project is a remake and focused evolution of the original [imou_life](https://github.com/user2684/imou_life) integration. It enhances the original [imouapi](https://github.com/user2684/imouapi) python library to communicate with Imou devices.

## 🎯 Main Focus

Unlike other integrations that try to cover every feature, this integration focuses specifically on **PTZ (Pan-Tilt-Zoom) functionality**. It is designed to make automating camera movements reliable and easy.

## ✨ Features

As of the current version, the integration supports the following specific features:

* **Camera Status:** Monitor if the camera is Online or Offline.
* **Restart Device:** Remotely reboot the camera via Home Assistant.
* **PTZ Favorites:** Quickly turn the camera lens to pre-defined "Favorite Points" (Presets) set in the Imou app.

## 💾 Installation

### Option 1: HACS (Recommended)
1. Ensure [HACS](https://hacs.xyz/) is installed.
2. Go to **HACS** -> **Integrations**.
3. Click the three dots on the top right corner and select **Custom repositories**.
4. Add the URL of this repository and select **Integration** as the category.
5. Click **Add**, then search for "Imou Camera PTZ" and install it.
6. Restart Home Assistant.

### Option 2: Manual
1. Download the `imou_cam_ptz` folder from the latest release.
2. Copy the folder into your Home Assistant `custom_components` directory (e.g., `/config/custom_components/imou_cam_ptz`).
3. Restart Home Assistant.

## ⚙️ Configuration

1. Go to **Settings** -> **Devices & Services**.
2. Click **+ Add Integration**.
3. Search for **Imou Camera PTZ**.
4. Enter your Imou App ID and App Secret (derived from the Imou Console).

## 🤖 Automations & Use Cases

The primary power of this integration is automating the camera angle based on home events.

### Example: Geolocation Surveillance
This example demonstrates how to rotate the camera to watch the parking spot when you arrive home, and rotate to watch the street view when you leave.

```yaml
# automation.yaml

- alias: Turn surveilance camera to parking position when at home
  description: ''
  triggers:
  - trigger: zone
    entity_id: device_tracker.my_iphone
    zone: zone.my_home
    event: enter
  conditions: []
  actions:
  - action: select.select_option
    metadata: {}
    target:
      entity_id: select.surveilance_cam_pt_lens_turncollection
    data:
      option: parking
  mode: single

- alias: Turn surveilance camera to street position when leaving home
  description: ''
  triggers:
  - trigger: zone
    entity_id: device_tracker.my_iphone
    zone: zone.my_home
    event: leave
  conditions: []
  actions:
  - action: select.select_option
    metadata: {}
    target:
      entity_id: select.surveilance_cam_pt_lens_turncollection
    data:
      option: street
  mode: single
```

## ❤️ Credits

This integration is heavily based on the work of [user2684](https://github.com/user2684).

 - Core logic based on: [imouapi](https://github.com/user2684/imouapi)
 - Original integration concept: [imou_life](https://github.com/user2684/imou_life)

## ⚠️ Disclaimer
This is a custom integration and is not affiliated with or endorsed by Imou. Use at your own risk.