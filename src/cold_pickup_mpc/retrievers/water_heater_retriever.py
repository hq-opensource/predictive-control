from datetime import datetime
from typing import Any, Dict

from cold_pickup_mpc.retrievers.api_calls import get_device_state, get_preferences_data
from cold_pickup_mpc.retrievers.device_retriever import DeviceRetriever
from cold_pickup_mpc.util.logging import LoggingUtil


logger = LoggingUtil.get_logger(__name__)


class WaterHeaterDataRetriever(DeviceRetriever):
    def _get_static_properties(self) -> Dict[str, Dict[str, Any]]:
        static_properties: Dict[str, Dict[str, Any]] = {
            "priority": {"type": int, "default": 1},
            "critical_state": {"type": float, "default": 40.0},
            "desired_state": {"type": float, "default": 90.0},
            "power_capacity": {"type": float, "default": 4.5},
            "critical_action": {"type": float, "default": 0.0},
            "activation_action": {"type": float, "default": 1.5},
            "deactivation_action": {"type": float, "default": 0.0},
            "tank_volume": {"type": float, "default": 270},  # default: 270 L
            "min_temperature": {"type": float, "default": 30},  # default: 30°C
            "max_temperature": {"type": float, "default": 90},  # default: 90°C
            "inlet_temperature": {"type": float, "default": 16},  # default: 16°C
            "water_heater_constant": {"type": float, "default": 4190 / 3600},  # Wh/°C/Litre
        }

        return static_properties

    def _load_dynamic_data(self, start: datetime, stop: datetime) -> Dict[str, Any]:
        initial_state: Dict[str, Any] = {}
        consumption_preferences: Dict[str, Any] = {}
        ambient_temperature: Dict[str, Any] = {}

        for device in self._devices:
            entity_id = device.get("entity_id", "unknown")

            # Build dictionary of initial states
            initial_state[entity_id] = get_device_state(entity_id, "water_heater_temperature")

            # Build dictionary of consumption preferences
            consumption_preferences[entity_id] = get_preferences_data(
                preferences_type="water-heater-consumption-preferences",
                device_id=entity_id,
                start=start,
                stop=stop,
            )

            # Build dictionary of ambient temperatures
            thermal_zone = device.get("thermal_zone")
            if thermal_zone:
                ambient_temperature[entity_id] = get_device_state(thermal_zone)
            else:
                logger.warning(
                    f"Device {entity_id} does not have a thermal zone associated with it. Using default value of 20.0"
                )
                ambient_temperature[entity_id] = 20.0

        data: Dict[str, Any] = {}
        data["initial_state"] = initial_state
        data["consumption_preferences"] = consumption_preferences
        data["ambient_temperature"] = ambient_temperature

        return data
