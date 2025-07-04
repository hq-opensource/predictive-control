"""This module provides functions for interacting with the Core API to manage devices.

It encapsulates various API calls related to device information, state retrieval,
and control actions such as setting setpoints and schedules. These functions
serve as the primary interface for the MPC system to communicate with and
control physical devices connected via the Core API.
"""

import os
from typing import Any, Dict

import requests

from cold_pickup_mpc.util.logging import LoggingUtil

# Configure and start the logger
logger = LoggingUtil.get_logger(__name__)
MPC_PRIORITY = 25


def get_devices() -> Dict[str, Any]:
    """Retrieves the installed devices from the Core API.

    This function sends a GET request to the /devices endpoint of the Core API
    to fetch a list of all installed devices.

    Returns:
        A dictionary containing the devices' information. The structure of the
        dictionary is expected to be defined by the Core API.

    Raises:
        requests.exceptions.HTTPError: If the API call fails (e.g., 4xx or 5xx status code).
    """
    api_url = f"{os.getenv('CORE_API_URL')}/devices"

    response = requests.get(api_url)
    response.raise_for_status()
    devices = response.json()
    logger.debug("Devices retrieved from API: %s", devices)
    return devices


def get_device_state(device_id: str, field: str | None = None) -> float:
    """Retrieves the state of a specific device from the Core API.

    This function sends a GET request to the /devices/state/{device_id} endpoint
    to get the current state of a given device. An optional 'field' parameter
    can be provided to retrieve a specific state attribute.

    Args:
        device_id: The unique identifier of the device.
        field: The specific state field to retrieve (e.g., 'temperature', 'soc').
               If None, the entire state object is returned.

    Returns:
        The state of the device as a float. If a 'field' is specified, it returns
        the value of that field. Otherwise, it might return a more complex object
        (though the type hint suggests float).

    Raises:
        requests.exceptions.HTTPError: If the API call fails.
    """
    api_url = f"{os.getenv('CORE_API_URL')}/devices/state/{device_id}"

    params = {}
    if field is not None:
        params = {"field": field}

    response = requests.get(api_url, params=params)
    response.raise_for_status()  # Raise an error for bad responses (4xx, 5xx)
    devices_state = response.json()
    return devices_state


def retrieve_total_consumption() -> Dict[str, Any] | None:
    """Retrieves the real-time total consumption of the building from the Core API.

    This function sends a GET request to the /building/consumption endpoint to
    get the current total energy consumption of the building.

    Returns:
        A dictionary containing the total consumption data, or None if the
        API call fails in a way that doesn't raise an exception but returns
        no data. The structure is defined by the Core API.

    Raises:
        requests.exceptions.HTTPError: If the API call fails.
    """
    api_url = f"{os.getenv('CORE_API_URL')}/building/consumption"

    response = requests.get(api_url)
    response.raise_for_status()  # Raise an error for bad responses (4xx, 5xx)
    total_consumption = response.json()
    return total_consumption


def write_setpoint(device_id: str, setpoint: float) -> None:
    """Writes a new setpoint for a specific device via the Core API.

    This function sends a POST request to the /devices/setpoint/{device_id}
    endpoint to update the setpoint of a device (e.g., setting a new
    target temperature for a thermostat).

    Args:
        device_id: The unique identifier of the device.
        setpoint: The new setpoint value to be written.

    Raises:
        requests.exceptions.HTTPError: If the API call fails.
    """
    api_url = f"{os.getenv('CORE_API_URL')}/devices/setpoint/{device_id}"

    params = {"setpoint": setpoint}
    response = requests.post(api_url, params=params)
    response.raise_for_status()  # Raise an error for bad responses (4xx, 5xx)


def write_schedule(schedule: Dict[str, Any]) -> None:
    """Writes a new schedule for devices via the Core API.

    This function sends a POST request to the /devices/schedule/{MPC_PRIORITY}
    endpoint to submit a new operational schedule for one or more devices.
    The schedule is assigned a priority level defined by MPC_PRIORITY.

    Args:
        schedule: A dictionary representing the schedule to be written. The
                  structure of this dictionary is defined by the Core API.

    Raises:
        requests.exceptions.HTTPError: If the API call fails.
    """
    api_url = f"{os.getenv('CORE_API_URL')}/devices/schedule/{MPC_PRIORITY}"
    response = requests.post(api_url, json=schedule)
    response.raise_for_status()  # Raise an error for bad responses (4xx, 5xx)
