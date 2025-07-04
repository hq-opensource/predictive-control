---
sidebar_position: 5
---

# Device Helper

This module provides a utility class, `DeviceHelper`, for managing and categorizing devices.

It defines an enumeration of standard device types used within the Cold Pickup MPC system, such as electric vehicles, electric storage, and space heating. Additionally, it offers static methods to perform common operations on device lists, including filtering devices by type or other keys, counting devices, and sorting them based on their assigned priorities. This helps in organizing and efficiently accessing device-related information throughout the application.

## Classes

### `DeviceHelper`

An enumeration that defines standard device types and provides helper utilities.

This class serves two purposes:
1. It provides a standardized set of identifiers for different types of controllable devices within the system (e.g., 'space_heating', 'electric_storage').
2. It offers a collection of static methods for common operations on lists of device dictionaries, such as filtering, counting, and sorting.

#### Methods

##### `device_exists(devices: List[Dict[str, Any]], device_id: str) -> bool`

Checks if a device with a specific ID exists in a list of devices.

**Args:**

- `devices`: A list of device dictionaries. Each dictionary is expected to have an 'entity_id' key.
- `device_id`: The ID of the device to search for.

**Returns:**

- `True` if a device with the given ID is found, `False` otherwise.

##### `get_all_device_info_by_key(devices: List[Dict[str, Any]], filter_key: str, filter_value: Any) -> List[Dict[str, Any]]`

Filters a list of devices based on a key-value pair.

This function returns a new list containing only the devices that have a specific value for a given key.

**Args:**

- `devices`: The list of device dictionaries to filter.
- `filter_key`: The key to be used for filtering (e.g., 'type', 'group').
- `filter_value`: The value that the `filter_key` should match.

**Returns:**

- A list of device dictionaries that match the filtering criteria.

##### `count_devices_by_type(device_list: List[Dict[str, Any]], device_type: str) -> int`

Counts the number of devices of a specific type in a list.

**Args:**

- `device_list`: The list of device dictionaries to search through.
- `device_type`: The device type to count (e.g., 'space_heating').

**Returns:**

- The total number of devices of the specified type.

##### `get_all_values_by_filtering_devices(device_list: List[Dict[str, Any]], filter_key: str, filter_value: str, target_key: str) -> List[str]`

Extracts values of a target key from devices matching a filter.

This function first filters a list of devices based on a key-value pair, and then collects the values of a specified target key from the filtered devices.

**Args:**

- `device_list`: The list of device dictionaries.
- `filter_key`: The key to filter by (e.g., 'type').
- `filter_value`: The value the `filter_key` should have.
- `target_key`: The key whose values are to be extracted (e.g., 'entity_id').

**Returns:**

- A list of values from the `target_key` for all matching devices.

##### `sort_devices_by_priorities(space_heating: bool, electric_storage: bool, electric_vehicle: bool, water_heater: bool) -> List[Dict[str, Any]]`

Sorts a list of active devices based on their assigned priorities.

This function first fetches all available devices, then filters them to include only the active device types specified by the boolean flags. Finally, it sorts the resulting list of devices in ascending order of their 'priority' value.

**Args:**

- `space_heating`: `True` if space heating devices should be included.
- `electric_storage`: `True` if electric storage devices should be included.
- `electric_vehicle`: `True` if electric vehicle devices should be included.
- `water_heater`: `True` if water heater devices should be included.

**Returns:**

- A list of device dictionaries, sorted by their priority.