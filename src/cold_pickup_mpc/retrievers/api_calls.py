import os

from datetime import datetime
from typing import Any, Dict, Optional

import requests

from cold_pickup_mpc.util.logging import LoggingUtil


# Configure and start the logger
logger = LoggingUtil.get_logger(__name__)


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
    else:
        params = None

    response = requests.get(api_url, params=params, timeout=30)
    response.raise_for_status()  # Raise an error for bad responses (4xx, 5xx)
    devices_state = response.json()
    return devices_state


def retrieve_total_consumption() -> Optional[Dict[str, Any]]:
    """Retrieves the real-time total consumption of the building."""
    api_url = f"{os.getenv('CORE_API_URL')}/building/consumption"

    response = requests.get(api_url)
    response.raise_for_status()
    total_consumption = response.json()
    return total_consumption


def get_preferences_data(
    preferences_type: str, device_id: str, start: datetime, stop: datetime
) -> Optional[Dict[str, Any]]:
    """Retrieves preferences data for a specified type and device over a time range.

    Args:
        preferences_type: The type of preferences data to retrieve, options:
        "setpoint-preferences", "occupancy_preferences", "electric-battery-soc-preferences", "vehicle-branched-preferences", "vehicle-soc-preferences".
        device_id: The ID of the device.
        start: The start timestamp (ISO 8601).
        stop: The stop timestamp (ISO 8601).
    """

    api_url = f"{os.getenv('CORE_API_URL')}/data/preferences/{preferences_type}"

    params = {"device_id": device_id, "start": start.isoformat(), "stop": stop.isoformat()}

    response = requests.get(api_url, params=params)
    response.raise_for_status()
    preferences_data = response.json()
    return preferences_data


def get_historical_data(
    historic_type: str, start: datetime, stop: datetime, device_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Retrieves historical data for a specified type over a time range.

    Args:
        historic_type: The type of historical data to retrieve. Possible values:
        "tz_temperature", "tz-historic-setpoint", "tz-electric-consumption", "non-controllable-loads", "vehicle-consumption".
        start: The start timestamp (ISO 8601).
        stop: The stop timestamp (ISO 8601).
        device_id: The ID of the device, if applicable (optional).

    Returns:
        A dictionary containing the historical data, or None if the request fails.
    """
    api_url = f"{os.getenv('CORE_API_URL')}/data/historic/{historic_type}"

    params = {"start": start.isoformat(), "stop": stop.isoformat()}
    if device_id is not None:
        params["device_id"] = device_id

    response = requests.get(api_url, params=params)
    response.raise_for_status()
    historical_data = response.json()
    return historical_data


def get_weather_historic(variable: str, start: datetime, stop: datetime) -> Dict[str, Any]:
    """
    Retrieves historic weather data from the Weather API.

    Args:
        variable (str): The weather variable to retrieve. Options include:
            - cloudBase
            - cloudCeiling
            - cloudCover
            - dewPoint
            - freezingRainIntensity
            - humidity
            - precipitationProbability
            - pressureSeaLevel
            - pressureSurfaceLevel
            - rainIntensity
            - sleetIntensity
            - snowIntensity
            - temperature
            - temperatureApparent
            - uvHealtConcern
            - uvIndex
            - visibility
            - weatherCode
            - windDirection
            - windGust
            - windSpeed
        start (datetime): Start timestamp in ISO 8601 format.
        stop (datetime): Stop timestamp in ISO 8601 format.

    Returns:
        Dict[str, Any]: A dictionary with weather data between the timestamps.

    Raises:
        requests.HTTPError: If the request fails.
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


def get_weather_forecast(variable: str, start: datetime, stop: datetime) -> Dict[str, Any]:
    """
    Retrieves weather forecast data from the Weather API.

    Args:
        variable (ForecastVariable): The weather variable to retrieve. Options:
            - cloudBase
            - cloudCeiling
            - cloudCover
            - dewPoint
            - evapotranspiration
            - freezingRainIntensity
            - humidity
            - iceAccumulation
            - iceAccumulationLwe
            - precipitationProbability
            - pressureSeaLevel
            - pressureSurfaceLevel
            - rainAccumulation
            - rainIntensity
            - sleetAccumulation
            - sleetAccumulationLwe
            - sleetIntensity
            - snowAccumulation
            - snowAccumulationLwe
            - snowDepth
            - snowIntensity
            - temperature
            - temperatureApparent
            - uvHealtConcern
            - uvIndex
            - visibility
            - weatherCode
            - windDirection
            - windGust
            - windSpeed
        start (datetime): Start timestamp in ISO 8601 format.
        stop (datetime): Stop timestamp in ISO 8601 format.

    Returns:
        Dict[str, Any]: A dictionary with weather forecast data between the timestamps.

    Raises:
        requests.HTTPError: If the request fails.
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
        logger.debug("Weather forecast data retrieved for '%s': %s", variable, forecast_data)
        return forecast_data
    except requests.RequestException as e:
        logger.error("Failed to retrieve weather forecast data: %s", e)
        raise


def get_non_controllable_loads_forecast(variable: str, start: datetime, stop: datetime) -> Dict[str, Any]:
    """
    Retrieves the non controallable loads from the Weather API.

    Args:
        variable (ForecastVariable): The weather variable to retrieve. Options:
            - non-controllable-loads

        start (datetime): Start timestamp in ISO 8601 format.
        stop (datetime): Stop timestamp in ISO 8601 format.

    Returns:
        Dict[str, Any]: A dictionary with the non controllable loads forecast data between the timestamps.

    Raises:
        requests.HTTPError: If the request fails.
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
        logger.debug("Non controllable loads forecast retrieved for '%s': %s", variable, forecast_data)
        return forecast_data
    except requests.RequestException as e:
        logger.error("Failed to retrieveNon controllable loads forecast data: %s", e)
        raise


def write_setpoint(device_id: str, setpoint: float) -> None:
    api_url = f"{os.getenv('CORE_API_URL')}/devices/setpoint/{device_id}"

    params = {"setpoint": setpoint}
    response = requests.post(api_url, params=params)
    response.raise_for_status()  # Raise an error for bad responses (4xx, 5xx)
