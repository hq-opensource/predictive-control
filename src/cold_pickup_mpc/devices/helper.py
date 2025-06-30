from enum import Enum
from typing import Any, Dict, List

from cold_pickup_mpc.devices.api_calls import get_devices


class DeviceHelper(Enum):
    """Enum that defines different device types.

    Every device created has a type associated with it. The type comes from this module.
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
        """
        Check if a device of the specified type exists in the list.

        :param devices: List of dictionaries representing devices.
        :param device_id: The ID of device to search for.
        :return: True if a device of the given ID exists, False otherwise.
        """
        return any(device.get("entity_id") == device_id for device in devices)

    @staticmethod
    def get_all_device_info_by_key(
        devices: List[Dict[str, Any]], filter_key: str, filter_value: Any
    ) -> List[Dict[str, Any]]:
        """
        Filter a list of devices based on a specified key and value.

        :param devices: List of dictionaries representing devices.
        :param filter_key: The key to filter on (e.g., 'type', 'group').
        :param filter_value: The value to match against for the specified key.
        :return: List of dictionaries where the filter_key matches filter_value.
        """
        filtered_devices = []
        for device in devices:
            if device.get(filter_key) == filter_value:
                filtered_devices.append(device)
        return filtered_devices

    @staticmethod
    def count_devices_by_type(device_list: List[Dict[str, Any]], device_type: str) -> int:
        """
        Count the number of devices of the specified type in the list.

        :param device_list: List of dictionaries representing devices.
        :param device_type: The type of device to count.
        :return: The number of devices of the given type.
        """
        return sum(device.get("type") == device_type for device in device_list)

    @staticmethod
    def get_all_values_by_filtering_devices(
        device_list: List[Dict[str, Any]], filter_key: str, filter_value: str, target_key: str
    ) -> List[str]:
        """
        Get all the values of the 'target_key' from the list of devices that have a 'filter_key'
        with the specified 'filter_value'.

        :param device_list: List of dictionaries representing devices.
        :param filter_key: The key to filter devices (e.g., 'type').
        :param filter_value: The value that the 'filter_key' should have (e.g., 'space_heating').
        :param target_key: The key whose values will be extracted (e.g., 'entity_id').
        :return: A list of all 'target_key' values where 'filter_key' matches 'filter_value'.
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
        """Sort devices by priority."""
        devices = get_devices()

        if not devices:
            return []

        # Verify that the devices have the 'priority' key
        devices_with_priority = [d for d in devices["content"] if "priority" in d]

        # Build the list of present devices based on the list of devices with priority
        present_devices_with_priority = []
        if space_heating:
            present_devices_with_priority.append(
                DeviceHelper.get_all_device_info_by_key(devices_with_priority, "type", DeviceHelper.SPACE_HEATING.value)
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
                    devices_with_priority, "type", DeviceHelper.ELECTRIC_VEHICLE_V1G.value
                )
            )
        if water_heater:
            present_devices_with_priority.append(
                DeviceHelper.get_all_device_info_by_key(devices_with_priority, "type", DeviceHelper.WATER_HEATER.value)
            )

        # Sort present devices by priority
        # Flatten the nested list of devices and sort by 'priority'
        sorted_existing_devices = sorted(
            [device for group in present_devices_with_priority for device in group],
            key=lambda device: device["priority"],
        )

        return sorted_existing_devices
