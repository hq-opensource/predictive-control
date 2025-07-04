from datetime import datetime
from typing import Any, Dict

from cold_pickup_mpc.retrievers.api_calls import get_device_state, get_preferences_data
from cold_pickup_mpc.retrievers.device_retriever import DeviceRetriever
from cold_pickup_mpc.util.logging import LoggingUtil

logger = LoggingUtil.get_logger(__name__)


class ElectricStorageDataRetriever(DeviceRetriever):
    """A concrete implementation of DeviceRetriever for electric storage devices.

    This class specializes in retrieving both static parameters and dynamic
    (time-series) data relevant to electric battery storage systems. It defines
    the default properties for electric storage and fetches their initial state
    of charge and SoC preferences from the Core API.
    """

    def _get_static_properties(self) -> Dict[str, Dict[str, Any]]:
        """Defines the static properties specific to electric storage devices.

        Returns:
            A dictionary specifying the name, type, and default value for each
            static property of an electric storage device (e.g., energy capacity,
            charging efficiency, min/max residual energy).
        """
        static_properties: Dict[str, Dict[str, Any]] = {
            "priority": {"type": int, "default": 13},
            "critical_state": {"type": float, "default": 20.0},
            "desired_state": {"type": float, "default": 90.0},
            "power_capacity": {"type": float, "default": 4.5},
            "critical_action": {"type": float, "default": 0.0},
            "activation_action": {"type": float, "default": 4.5},
            "deactivation_action": {"type": float, "default": 0.0},
            "modulation_capability": {"type": bool, "default": True},
            "discharge_capability": {"type": bool, "default": True},
            "discharge_action": {"type": float, "default": -4.5},
            "final_soc_requirement": {"type": float, "default": 50.0},
            "energy_capacity": {"type": float, "default": 15.0},
            "charging_efficiency": {"type": float, "default": 0.98},
            "discharging_efficiency": {"type": float, "default": 0.98},
            "min_residual_energy": {"type": float, "default": 30},
            "max_residual_energy": {"type": float, "default": 95},
            "decay_factor": {"type": float, "default": 0.995},
        }

        return static_properties

    def _load_dynamic_data(self, start: datetime, stop: datetime) -> Dict[str, Any]:
        """Loads dynamic (time-series) data for electric storage devices.

        This method fetches the initial state of charge (SoC) for each electric
        storage device and their SoC preference profiles over the specified time range
        from the Core API.

        Args:
            start: The start datetime for the dynamic data.
            stop: The stop datetime for the dynamic data.

        Returns:
            A dictionary containing the initial SoC and SoC preferences for all
            configured electric storage devices.
        """
        initial_state: Dict[str, Any] = {}
        soc_preferences: Dict[str, Any] = {}

        for device in self._devices:
            entity_id = device.get("entity_id", "unknown")

            # Build dictionary of initial states
            initial_state[entity_id] = get_device_state(
                entity_id, "electric_storage_soc"
            )

            # Build dictionary of setpoint preferences
            soc_preferences[entity_id] = get_preferences_data(
                preferences_type="electric-battery-soc-preferences",
                device_id=entity_id,
                start=start,
                stop=stop,
            )

        data: Dict[str, Any] = {}
        data["initial_state"] = initial_state
        data["soc_preferences"] = soc_preferences

        return data
