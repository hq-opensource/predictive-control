from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Type, TypeVar

from cold_pickup_mpc.util.logging import LoggingUtil

logger = LoggingUtil.get_logger(__name__)
T = TypeVar("T", str, bool, int, float)


class DeviceRetriever(ABC):
    """Abstract base class for retrieving data related to devices.

    This class defines a common interface for fetching both static properties
    and dynamic (time-series) data for various devices. Subclasses must implement
    methods to define their specific static properties and how to load their
    dynamic data.
    """

    _devices: List[Dict[str, Any]]

    def __init__(self, devices: List[Dict[str, Any]]) -> None:
        """Initializes the DeviceRetriever with a list of device configurations.

        Args:
            devices: A list of dictionaries, where each dictionary represents
                     a device and its configuration.
        """
        self._devices = devices

    def retrieve_data(self, start: datetime, stop: datetime) -> Dict[str, Any]:
        """Retrieves all necessary data (static and dynamic) for the devices.

        This method orchestrates the data retrieval process. It first gathers
        static properties for each device and then loads dynamic time-series data
        for the specified time range.

        Args:
            start: The start datetime for retrieving dynamic data.
            stop: The stop datetime for retrieving dynamic data.

        Returns:
            A dictionary containing all retrieved data, organized by property name
            or data type.
        """
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
        """Abstract method to load dynamic (time-series) data for the devices.

        Subclasses must implement this method to define how they retrieve
        time-dependent data (e.g., sensor readings, forecasts) for their specific
        device types.

        Args:
            start: The start datetime for the dynamic data.
            stop: The stop datetime for the dynamic data.

        Returns:
            A dictionary containing the dynamic data.
        """
        pass

    @abstractmethod
    def _get_static_properties(self) -> Dict[str, Dict[str, Any]]:
        """Abstract method to define the static properties of the devices.

        Subclasses must implement this method to return a dictionary specifying
        the names, expected types, and default values for static properties
        (e.g., capacity, efficiency) relevant to their device type.

        Returns:
            A dictionary where keys are property names and values are dictionaries
            containing 'type' (the expected Python type) and 'default' (the default value).
        """
        pass

    def _get_static_property_value(
        self,
        device: Dict[str, Any],
        property_name: str,
        default_value: T,
        property_type: Type[T],
    ) -> T:
        """Helper function to safely retrieve a static property value from a device dictionary.

        This method attempts to extract a property value from a device's configuration
        dictionary and cast it to the specified type. If the property is missing or
        cannot be converted, it logs a warning and returns a default value.

        Args:
            device: The dictionary representing a single device's configuration.
            property_name: The name of the static property to retrieve.
            default_value: The default value to return if the property is not found or invalid.
            property_type: The expected Python type of the property (e.g., `int`, `float`, `bool`).

        Returns:
            The retrieved property value, cast to the specified type, or the default value.
        """
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
