from datetime import datetime
from typing import Any, Dict

from cold_pickup_mpc.retrievers.api_calls import get_device_state, get_preferences_data
from cold_pickup_mpc.retrievers.device_retriever import DeviceRetriever
from cold_pickup_mpc.util.logging import LoggingUtil


logger = LoggingUtil.get_logger(__name__)


class ElectricStorageDataRetriever(DeviceRetriever):
    def _get_static_properties(self) -> Dict[str, Dict[str, Any]]:
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
        initial_state: Dict[str, Any] = {}
        soc_preferences: Dict[str, Any] = {}

        for device in self._devices:
            entity_id = device.get("entity_id", "unknown")

            # Build dictionary of initial states
            initial_state[entity_id] = get_device_state(entity_id, "electric_storage_soc")

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
