"""Constants for imouapi"""

# default connection timeout
DEFAULT_TIMEOUT = 10

# max api retries
MAX_RETRIES = 3

# how long to wait in seconds for the image to be available before downloading it
CAMERA_WAIT_BEFORE_DOWNLOAD = 1.5

# for dormant devices for how long to wait in seconds after waking the device up
WAIT_AFTER_WAKE_UP = 4.0

# Device online status mapping
ONLINE_STATUS = {
    "0": "Offline",
    "1": "Online",
    "4": "Dormant",
    "UNKNOWN": "Unknown",
}

# PTZ operation mapping
PTZ_OPERATIONS = {
    "UP": 0,
    "DOWN": 1,
    "LEFT": 2,
    "RIGHT": 3,
    "UPPER_LEFT": 4,
    "BOTTOM_LEFT": 5,
    "UPPER_RIGHT": 6,
    "BOTTOM_RIGHT": 7,
    "ZOOM_IN": 8,
    "ZOOM_OUT": 9,
    "STOP": 10,
}

# buttons supported by this library
BUTTONS = {
    "restartDevice": "Restart device",
    "turnCollection": "Turn to"
}

# sensors supported by this library
SENSORS = {
    "status": "Status",
}

# select supported by this library
SELECTS = {
    "turnCollection": "Turn to favourite point",
}