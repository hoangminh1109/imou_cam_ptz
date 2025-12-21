"""Constants for imou_cam_ptz"""

# Internal constants
DOMAIN = "imou_cam_ptz"
PLATFORMS = ["button", "select", "sensor"]

# Configuration definitions
CONF_API_URL = "api_url"
CONF_CHANNEL_NAME = "channel_name"
CONF_APP_ID = "app_id"
CONF_APP_SECRET = "app_secret"
CONF_DISCOVERED_CHANNEL = "discovered_channel"
CONF_DEVICE_ID = "device_id"
CONF_CHANNEL_ID = "channel_id"

OPTION_API_TIMEOUT = "api_timeout"
OPTION_API_URL = "api_url"
OPTION_CAMERA_WAIT_BEFORE_DOWNLOAD = "camera_wait_before_download"
OPTION_WAIT_AFTER_WAKE_UP = "wait_after_wakeup"
OPTION_SCAN_INTERVAL = "scan_interval"

# Defaults
DEFAULT_API_URL = "https://openapi.easy4ip.com/openapi"
DEFAULT_SCAN_INTERVAL = 15 * 60

# icons of the sensors
SENSOR_ICONS = {
    "__default__": "mdi:bookmark",
    "restartDevice": "mdi:restart",
    "turnCollection": "mdi:cctv",
    "status": "mdi:lan-connect",
}

