from datetime import datetime
from typing import Any, Dict

import requests

from cold_pickup_mpc.retrievers.api_calls import (
    get_solar_forecast,
    get_weather_forecast,
)
from cold_pickup_mpc.retrievers.device_retriever import DeviceRetriever
from cold_pickup_mpc.util.logging import LoggingUtil

logger = LoggingUtil.get_logger(__name__)


class PhotovoltaicGeneratorDataRetriever(DeviceRetriever):
    """A concrete implementation of DeviceRetriever for photovoltaic devices.

    This class specializes in retrieving both static parameters and dynamic
    (time-series) data relevant to photovoltaic panels. It defines the default
    properties for photovoltaic generators and fetches the GHI, DNI and DHI.
    """

    def _get_static_properties(self) -> Dict[str, Dict[str, Any]]:
        """Defines the static properties specific to photovoltaic generators devices.

        Returns:
            A dictionary specifying the name, type, and default value for each
            static property of a photovoltaic generators devices (e.g., pv model,
            inverter model, strings, etc.).
        """
        static_properties: Dict[str, Dict[str, Any]] = {
            "inverter": {
                "type": str,
                "default": "Schneider_Electric_Solar_Inc___XW_Pro_6848_NA__240V_",
            },
            "pv_module": {"type": str, "default": "Canadian_Solar_Inc__CS6k_280M"},
            "modules_per_string": {"type": int, "default": 8},
            "strings_per_inverter": {"type": int, "default": 2},
            "surface_tilt": {"type": int, "default": 45},
        }

        return static_properties

    def _load_dynamic_data(self, start: datetime, stop: datetime) -> Dict[str, Any]:
        """Loads dynamic (time-series) data for photovoltaic generators devices.

        This method fetches the initial water temperature, hot water consumption
        preferences, and ambient temperature for each photovoltaic generators from the Core API
        over the specified time range. It also handles cases where a thermal zone
        might not be associated with a photovoltaic generators.

        Args:
            start: The start datetime for the dynamic data.
            stop: The stop datetime for the dynamic data.

        Returns:
            A dictionary containing the initial state, consumption preferences,
            and ambient temperature for all configured photovoltaic generatorss.
        """

        # Retrieve solar forecast
        weather_forecast: Dict[str, Any] = {}
        try:
            weather_forecast["ghi"] = get_solar_forecast(
                variable="clear_sky_ghi",
                start=start,
                stop=stop,
            )
        except requests.RequestException:
            logger.error("Failed to retrieve solar forecast for ghi. Skipping.")
        try:
            weather_forecast["dni"] = get_solar_forecast(
                variable="clear_sky_dni",
                start=start,
                stop=stop,
            )
        except requests.RequestException:
            logger.error("Failed to retrieve solar forecast for dni. Skipping.")
        try:
            weather_forecast["dhi"] = get_solar_forecast(
                variable="clear_sky_dhi",
                start=start,
                stop=stop,
            )
        except requests.RequestException:
            logger.error("Failed to retrieve solar forecast for dhi. Skipping.")

        # Retrieve weather forecast
        try:
            # Retrieve temperature
            temperature = get_weather_forecast(
                variable="temperature",
                start=start,
                stop=stop,
            )
            weather_forecast["temperature"] = temperature
        except requests.RequestException:
            logger.error(
                "Failed to retrieve weather forecast for temperature. Skipping."
            )

        try:
            # Retrieve wind speed
            wind_speed = get_weather_forecast(
                variable="windSpeed",
                start=start,
                stop=stop,
            )
            weather_forecast["wind_speed"] = wind_speed
        except requests.RequestException:
            logger.error(
                "Failed to retrieve weather forecast for wind speed. Skipping."
            )

        return weather_forecast
