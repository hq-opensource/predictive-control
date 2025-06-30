from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Type, TypeVar

from cold_pickup_mpc.util.logging import LoggingUtil


logger = LoggingUtil.get_logger(__name__)
T = TypeVar("T", str, bool, int, float)


class DeviceRetriever(ABC):
    _devices: List[Dict[str, Any]]

    def __init__(self, devices: List[Dict[str, Any]]) -> None:
        self._devices = devices

    def retrieve_data(self, start: datetime, stop: datetime) -> Dict[str, Any]:
        data: Dict = {}

        static_properties = self._get_static_properties()

        for property_name, property_info in static_properties.items():
            property_type = property_info["type"]
            default_value = property_info["default"]

            properties = {}
            for device in self._devices:
                entity_id = device.get("entity_id")
                properties[entity_id] = self._get_static_property_value(
                    device, property_name, default_value, property_type
                )

            data[property_name] = properties

        dynamic_data = self._load_dynamic_data(start, stop)

        data.update(dynamic_data)

        return data

    @abstractmethod
    def _load_dynamic_data(self, start: datetime, stop: datetime) -> Dict[str, Any]:
        pass

    @abstractmethod
    def _get_static_properties(self) -> Dict[str, Dict[str, Any]]:
        pass

    def _get_static_property_value(
        self, device: Dict[str, Any], property_name: str, default_value: T, property_type: Type[T]
    ) -> T:
        """Helper function to get static property value from device."""
        try:
            return property_type(device[property_name])
        except (KeyError, TypeError, ValueError):
            logger.warning(
                "%s not found for entity_id '%s'. Using default value %s.",
                property_name,
                device.get("entity_id", "unknown"),
                default_value,
            )
            return default_value
