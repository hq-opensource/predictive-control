import os
from datetime import datetime
from typing import Any, Dict, Optional

import requests

from cold_pickup_mpc.util.logging import LoggingUtil

# Configure and start the logger
logger = LoggingUtil.get_logger(__name__)


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

    params = {"field": field} if field is not None else None

    response = requests.get(api_url, params=params, timeout=30)
    response.raise_for_status()  # Raise an error for bad responses (4xx, 5xx)
    devices_state = response.json()
    return devices_state


def retrieve_total_consumption() -> Optional[Dict[str, Any]]:
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
    response.raise_for_status()
    total_consumption = response.json()
    return total_consumption


def get_preferences_data(
    preferences_type: str, device_id: str, start: datetime, stop: datetime
) -> Optional[Dict[str, Any]]:
    """Retrieves preferences data for a specified type and device over a time range from the Core API.

    This function fetches various types of preference data (e.g., setpoints, occupancy,
    battery SoC preferences) for a given device within a specified time window.

    Args:
        preferences_type: The type of preferences data to retrieve. Possible options include:
                          "setpoint-preferences", "occupancy_preferences",
                          "electric-battery-soc-preferences", "vehicle-branched-preferences",
                          "vehicle-soc-preferences".
        device_id: The ID of the device for which to retrieve preferences.
        start: The start timestamp of the desired time range.
        stop: The stop timestamp of the desired time range.

    Returns:
        A dictionary containing the preferences data, or None if the request fails
        in a way that doesn't raise an exception but returns no data.

    Raises:
        requests.exceptions.HTTPError: If the API call fails.
    """

    api_url = f"{os.getenv('CORE_API_URL')}/data/preferences/{preferences_type}"

    params = {
        "device_id": device_id,
        "start": start.isoformat(),
        "stop": stop.isoformat(),
    }

    response = requests.get(api_url, params=params)
    response.raise_for_status()
    preferences_data = response.json()
    return preferences_data


def get_historical_data(
    historic_type: str, start: datetime, stop: datetime, device_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Retrieves historical data for a specified type over a time range from the Core API.

    This function fetches various types of historical data (e.g., zone temperature,
    electric consumption) for a given time window. An optional `device_id` can
    be provided to filter data for a specific device.

    Args:
        historic_type: The type of historical data to retrieve. Possible values include:
                       "tz_temperature", "tz-historic-setpoint", "tz-electric-consumption",
                       "non-controllable-loads", "vehicle-consumption".
        start: The start timestamp of the desired time range.
        stop: The stop timestamp of the desired time range.
        device_id: The ID of the device, if applicable (optional).

    Returns:
        A dictionary containing the historical data, or None if the request fails
        in a way that doesn't raise an exception but returns no data.

    Raises:
        requests.exceptions.HTTPError: If the API call fails.
    """
    api_url = f"{os.getenv('CORE_API_URL')}/data/historic/{historic_type}"

    params = {"start": start.isoformat(), "stop": stop.isoformat()}
    if device_id is not None:
        params["device_id"] = device_id

    response = requests.get(api_url, params=params)
    response.raise_for_status()
    historical_data = response.json()
    return historical_data


def get_weather_historic(
    variable: str, start: datetime, stop: datetime
) -> Dict[str, Any]:
    """Retrieves historic weather data from the Core API's weather endpoint.

    This function fetches historical weather observations for a specified variable
    within a given time range.

    Args:
        variable: The weather variable to retrieve (e.g., "temperature", "humidity").
                  Refer to the Core API documentation for a full list of supported variables.
        start: The start timestamp of the desired historical period.
        stop: The stop timestamp of the desired historical period.

    Returns:
        A dictionary containing the historical weather data. The structure of the
        dictionary is defined by the Core API.

    Raises:
        requests.exceptions.RequestException: If the API call fails due to network issues,
                                              invalid response, or HTTP errors.
    """
    api_url = f"{os.getenv('CORE_API_URL')}/data/weather/historic/{variable}"
    params = {
        "start": start.isoformat(),
        "stop": stop.isoformat(),
    }

    try:
        response = requests.get(api_url, params=params, timeout=30)
        response.raise_for_status()
        weather_data = response.json()
        logger.debug("Weather data retrieved for '%s': %s", variable, weather_data)
        return weather_data
    except requests.RequestException as e:
        logger.error("Failed to retrieve weather data: %s", e)
        raise


def get_weather_forecast(
    variable: str, start: datetime, stop: datetime
) -> Dict[str, Any]:
    """Retrieves weather forecast data from the Core API's weather endpoint.

    This function fetches predicted weather data for a specified variable
    within a given future time range.

    Args:
        variable: The weather variable to retrieve (e.g., "temperature", "humidity").
                  Refer to the Core API documentation for a full list of supported variables.
        start: The start timestamp of the desired forecast period.
        stop: The stop timestamp of the desired forecast period.

    Returns:
        A dictionary containing the weather forecast data. The structure of the
        dictionary is defined by the Core API.

    Raises:
        requests.exceptions.RequestException: If the API call fails due to network issues,
                                              invalid response, or HTTP errors.
    """
    api_url = f"{os.getenv('CORE_API_URL')}/data/weather/forecast/{variable}"
    params = {
        "start": start.isoformat(),
        "stop": stop.isoformat(),
    }

    try:
        response = requests.get(api_url, params=params, timeout=30)
        response.raise_for_status()
        forecast_data = response.json()
        logger.debug(
            "Weather forecast data retrieved for '%s': %s", variable, forecast_data
        )
        return forecast_data
    except requests.RequestException as e:
        logger.error("Failed to retrieve weather forecast data: %s", e)
        raise


def get_non_controllable_loads_forecast(
    variable: str, start: datetime, stop: datetime
) -> Dict[str, Any]:
    """Retrieves the forecast for non-controllable loads from the Core API.

    This function fetches predicted data for loads that cannot be directly
    controlled by the MPC (e.g., base building consumption).

    Args:
        variable: The specific variable for non-controllable loads (e.g., "non-controllable-loads").
        start: The start timestamp of the desired forecast period.
        stop: The stop timestamp of the desired forecast period.

    Returns:
        A dictionary containing the non-controllable loads forecast data. The structure
        of the dictionary is defined by the Core API.

    Raises:
        requests.exceptions.RequestException: If the API call fails due to network issues,
                                              invalid response, or HTTP errors.
    """
    api_url = f"{os.getenv('CORE_API_URL')}/data/forecast/{variable}"
    params = {
        "start": start.isoformat(),
        "stop": stop.isoformat(),
    }

    try:
        response = requests.get(api_url, params=params, timeout=30)
        response.raise_for_status()
        forecast_data = response.json()
        logger.debug(
            "Non controllable loads forecast retrieved for '%s': %s",
            variable,
            forecast_data,
        )
        return forecast_data
    except requests.RequestException as e:
        logger.error("Failed to retrieveNon controllable loads forecast data: %s", e)
        raise


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
