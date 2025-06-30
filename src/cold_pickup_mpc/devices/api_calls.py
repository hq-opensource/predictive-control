import os

from typing import Any, Dict

import requests

from cold_pickup_mpc.util.logging import LoggingUtil


# Configure and start the logger
logger = LoggingUtil.get_logger(__name__)
MPC_PRIORITY = 25


def get_devices() -> Dict[str, Any]:
    """Retrieves the installed devices from the Core API."""
    api_url = f"{os.getenv('CORE_API_URL')}/devices"

    response = requests.get(api_url)
    response.raise_for_status()
    devices = response.json()
    logger.debug("Devices retrieved from API: %s", devices)
    return devices


def get_device_state(device_id: str, field: str | None = None) -> float:
    api_url = f"{os.getenv('CORE_API_URL')}/devices/state/{device_id}"

    if field is not None:
        params = {"field": field}

    response = requests.get(api_url, params=params)
    response.raise_for_status()  # Raise an error for bad responses (4xx, 5xx)
    devices_state = response.json()
    return devices_state


def retrieve_total_consumption() -> Dict[str, Any] | None:
    """Retrieves the real-time total consumption of the building."""
    api_url = f"{os.getenv('CORE_API_URL')}/building/consumption"

    response = requests.get(api_url)
    response.raise_for_status()  # Raise an error for bad responses (4xx, 5xx)
    total_consumption = response.json()
    return total_consumption


def write_setpoint(device_id: str, setpoint: float) -> None:
    api_url = f"{os.getenv('CORE_API_URL')}/devices/setpoint/{device_id}"

    params = {"setpoint": setpoint}
    response = requests.post(api_url, params=params)
    response.raise_for_status()  # Raise an error for bad responses (4xx, 5xx)


def write_schedule(schedule: Dict[str, Any]) -> None:
    api_url = f"{os.getenv('CORE_API_URL')}/devices/schedule/{MPC_PRIORITY}"
    response = requests.post(api_url, json=schedule)
    response.raise_for_status()  # Raise an error for bad responses (4xx, 5xx)
