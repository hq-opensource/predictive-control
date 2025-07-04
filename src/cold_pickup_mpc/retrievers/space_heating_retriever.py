from datetime import datetime, timedelta
from typing import Any, Dict

from cold_pickup_mpc.retrievers.api_calls import (
    get_device_state,
    get_preferences_data,
    get_weather_forecast,
)
from cold_pickup_mpc.retrievers.device_retriever import DeviceRetriever
from cold_pickup_mpc.thermal_model.learn_thermal_model import LearnThermalDynamics
from cold_pickup_mpc.util.logging import LoggingUtil

logger = LoggingUtil.get_logger(__name__)


class SpaceHeatingDataRetriever(DeviceRetriever):
    """A concrete implementation of DeviceRetriever for space heating devices (smart thermostats).

    This class specializes in retrieving both static parameters and dynamic
    (time-series) data relevant to space heating systems. It defines the default
    properties for space heating zones and fetches their initial temperature,
    setpoint preferences, occupancy preferences, and weather forecasts from the
    Core API. It also incorporates a thermal model learning component.
    """

    def _get_static_properties(self) -> Dict[str, Dict[str, Any]]:
        """Defines the static properties specific to space heating devices.

        Returns:
            A dictionary specifying the name, type, and default value for each
            static property of a space heating device (e.g., priority, min/max setpoint).
        """
        static_properties: Dict[str, Dict[str, Any]] = {
            "priority": {"type": int, "default": 1},
            "min_setpoint": {"type": float, "default": 15.0},
            "max_setpoint": {"type": float, "default": 25.0},
        }

        return static_properties

    def _load_dynamic_data(self, start: datetime, stop: datetime) -> Dict[str, Any]:
        """Loads dynamic (time-series) data for space heating devices.

        This method fetches the initial temperature, setpoint preferences, and
        occupancy preferences for each space heating device from the Core API
        over the specified time range. It also retrieves the temperature forecast
        and triggers the learning of the thermal model.

        Args:
            start: The start datetime for the dynamic data.
            stop: The stop datetime for the dynamic data.

        Returns:
            A dictionary containing the initial state, setpoint preferences,
            occupancy preferences, thermal model, and weather forecast for
            all configured space heating devices.
        """
        initial_state: Dict[str, Any] = {}
        setpoint_preferences: Dict[str, Any] = {}
        occupancy_preferences: Dict[str, Any] = {}

        for device in self._devices:
            entity_id = device.get("entity_id", "unknown")

            # Build dictionary of initial states
            initial_state[entity_id] = get_device_state(entity_id)

            # Build dictionary of setpoint preferences
            setpoint_preferences[entity_id] = get_preferences_data(
                preferences_type="setpoint-preferences",
                device_id=entity_id,
                start=start,
                stop=stop,
            )

            # Build dictionary of occupancy preferences
            occupancy_preferences[entity_id] = get_preferences_data(
                preferences_type="occupancy_preferences",
                device_id=entity_id,
                start=start,
                stop=stop,
            )

        # Retrieve weather forecast
        weather_forecast = {}
        temperature = get_weather_forecast(
            variable="temperature",
            start=start,
            stop=stop,
        )
        weather_forecast["temperature"] = temperature

        data: Dict[str, Any] = {}
        data["initial_state"] = initial_state
        data["setpoint_preferences"] = setpoint_preferences
        data["occupancy_preferences"] = occupancy_preferences

        # Save thermal model
        data["thermal_model"] = self._learn_thermal_model(days_in_the_past=10)

        # Save weather forecast
        data["weather_forecast"] = weather_forecast

        return data

    def _learn_thermal_model(self, days_in_the_past: int) -> Dict[str, Any]:
        """Learns or validates the thermal model for the space heating zones.

        This method initiates the process of learning a thermal dynamics model
        for the building's thermal zones based on historical data. The model
        is crucial for predicting indoor temperature changes in the MPC.

        Args:
            days_in_the_past: The number of past days to consider for learning
                              the thermal model.

        Returns:
            A dictionary containing the learned or validated thermal model parameters.
        """
        # Learning the thermal model takes time. Where to execute this? As a schedule?
        start = datetime.now().astimezone() - timedelta(days=days_in_the_past)
        stop = (
            datetime.now()
            .astimezone()
            .replace(hour=0, minute=0, second=0, microsecond=0)
        )
        learn_thermal_dynamics = LearnThermalDynamics()
        thermal_model = learn_thermal_dynamics.validate_or_learn_model(start, stop)
        return thermal_model
