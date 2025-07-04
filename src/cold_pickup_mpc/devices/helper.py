from enum import Enum
from typing import Any, Dict, List

from cold_pickup_mpc.devices.api_calls import get_devices


class DeviceHelper(Enum):
    """An enumeration that defines standard device types and provides helper utilities.

    This class serves two purposes:
    1. It provides a standardized set of identifiers for different types of
       controllable devices within the system (e.g., 'space_heating', 'electric_storage').
    2. It offers a collection of static methods for common operations on lists
       of device dictionaries, such as filtering, counting, and sorting.
    """

    ON_OFF_EV_CHARGER = "on_off_ev_charger"
    ELECTRIC_VEHICLE_V1G = "electric_vehicle_v1g"
    ELECTRIC_VEHICLE_V2G = "electric_vehicle_v2g"
    ELECTRIC_STORAGE = "electric_storage"
    PHOTOVOLTAIC_GENERATOR_PVLIB = "photovoltaic_generator_pvlib"
    SPACE_HEATING = "space_heating"
    THERMAL_STORAGE = "thermal_storage"
    WATER_HEATER = "water_heater"

    @staticmethod
    def device_exists(devices: List[Dict[str, Any]], device_id: str) -> bool:
        """Checks if a device with a specific ID exists in a list of devices.

        Args:
            devices: A list of device dictionaries. Each dictionary is expected
                     to have an 'entity_id' key.
            device_id: The ID of the device to search for.

        Returns:
            True if a device with the given ID is found, False otherwise.
        """
        return any(device.get("entity_id") == device_id for device in devices)

    @staticmethod
    def get_all_device_info_by_key(
        devices: List[Dict[str, Any]], filter_key: str, filter_value: Any
    ) -> List[Dict[str, Any]]:
        """Filters a list of devices based on a key-value pair.

        This function returns a new list containing only the devices that have
        a specific value for a given key.

        Args:
            devices: The list of device dictionaries to filter.
            filter_key: The key to be used for filtering (e.g., 'type', 'group').
            filter_value: The value that the `filter_key` should match.

        Returns:
            A list of device dictionaries that match the filtering criteria.
        """
        filtered_devices = []
        for device in devices:
            if device.get(filter_key) == filter_value:
                filtered_devices.append(device)
        return filtered_devices

    @staticmethod
    def count_devices_by_type(
        device_list: List[Dict[str, Any]], device_type: str
    ) -> int:
        """Counts the number of devices of a specific type in a list.

        Args:
            device_list: The list of device dictionaries to search through.
            device_type: The device type to count (e.g., 'space_heating').

        Returns:
            The total number of devices of the specified type.
        """
        return sum(device.get("type") == device_type for device in device_list)

    @staticmethod
    def get_all_values_by_filtering_devices(
        device_list: List[Dict[str, Any]],
        filter_key: str,
        filter_value: str,
        target_key: str,
    ) -> List[str]:
        """Extracts values of a target key from devices matching a filter.

        This function first filters a list of devices based on a key-value pair,
        and then collects the values of a specified target key from the filtered devices.

        Args:
            device_list: The list of device dictionaries.
            filter_key: The key to filter by (e.g., 'type').
            filter_value: The value the `filter_key` should have.
            target_key: The key whose values are to be extracted (e.g., 'entity_id').

        Returns:
            A list of values from the `target_key` for all matching devices.
        """
        return [
            device.get(target_key)
            for device in device_list
            if device.get(filter_key) == filter_value and target_key in device
        ]

    @staticmethod
    def sort_devices_by_priorities(
        space_heating: bool,
        electric_storage: bool,
        electric_vehicle: bool,
        water_heater: bool,
    ) -> List[Dict[str, Any]]:
        """Sorts a list of active devices based on their assigned priorities.

        This function first fetches all available devices, then filters them to
        include only the active device types specified by the boolean flags.
        Finally, it sorts the resulting list of devices in ascending order of
        their 'priority' value.

        Args:
            space_heating: True if space heating devices should be included.
            electric_storage: True if electric storage devices should be included.
            electric_vehicle: True if electric vehicle devices should be included.
            water_heater: True if water heater devices should be included.

        Returns:
            A list of device dictionaries, sorted by their priority.
        """
        devices = get_devices()

        if not devices or "content" not in devices:
            return []

        # Verify that the devices have the 'priority' key
        devices_with_priority = [d for d in devices["content"] if "priority" in d]

        # Build the list of present devices based on the list of devices with priority
        present_devices_with_priority = []
        if space_heating:
            present_devices_with_priority.append(
                DeviceHelper.get_all_device_info_by_key(
                    devices_with_priority, "type", DeviceHelper.SPACE_HEATING.value
                )
            )
        if electric_storage:
            present_devices_with_priority.append(
                DeviceHelper.get_all_device_info_by_key(
                    devices_with_priority, "type", DeviceHelper.ELECTRIC_STORAGE.value
                )
            )
        if electric_vehicle:
            present_devices_with_priority.append(
                DeviceHelper.get_all_device_info_by_key(
                    devices_with_priority,
                    "type",
                    DeviceHelper.ELECTRIC_VEHICLE_V1G.value,
                )
            )
        if water_heater:
            present_devices_with_priority.append(
                DeviceHelper.get_all_device_info_by_key(
                    devices_with_priority, "type", DeviceHelper.WATER_HEATER.value
                )
            )

        # Sort present devices by priority
        # Flatten the nested list of devices and sort by 'priority'
        sorted_existing_devices = sorted(
            [device for group in present_devices_with_priority for device in group],
            key=lambda device: device["priority"],
        )

        return sorted_existing_devices
