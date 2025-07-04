---
sidebar_position: 1
---

# API Calls

This module provides functions for interacting with the Core API to manage devices.

It encapsulates various API calls related to device information, state retrieval, and control actions such as setting setpoints and schedules. These functions serve as the primary interface for the MPC system to communicate with and control physical devices connected via the Core API.

## Functions

### `get_devices()`

Retrieves the installed devices from the Core API.

This function sends a GET request to the `/devices` endpoint of the Core API to fetch a list of all installed devices.

**Returns:**

- A dictionary containing the devices' information. The structure of the dictionary is expected to be defined by the Core API.

**Raises:**

- `requests.exceptions.HTTPError`: If the API call fails (e.g., 4xx or 5xx status code).

### `get_device_state(device_id: str, field: str | None = None)`

Retrieves the state of a specific device from the Core API.

This function sends a GET request to the `/devices/state/{device_id}` endpoint to get the current state of a given device. An optional 'field' parameter can be provided to retrieve a specific state attribute.

**Args:**

- `device_id`: The unique identifier of the device.
- `field`: The specific state field to retrieve (e.g., 'temperature', 'soc'). If None, the entire state object is returned.

**Returns:**

- The state of the device as a float. If a 'field' is specified, it returns the value of that field. Otherwise, it might return a more complex object.

**Raises:**

- `requests.exceptions.HTTPError`: If the API call fails.

### `retrieve_total_consumption()`

Retrieves the real-time total consumption of the building from the Core API.

This function sends a GET request to the `/building/consumption` endpoint to get the current total energy consumption of the building.

**Returns:**

- A dictionary containing the total consumption data, or None if the API call fails in a way that doesn't raise an exception but returns no data. The structure is defined by the Core API.

**Raises:**

- `requests.exceptions.HTTPError`: If the API call fails.

### `write_setpoint(device_id: str, setpoint: float)`

Writes a new setpoint for a specific device via the Core API.

This function sends a POST request to the `/devices/setpoint/{device_id}` endpoint to update the setpoint of a device (e.g., setting a new target temperature for a thermostat).

**Args:**

- `device_id`: The unique identifier of the device.
- `setpoint`: The new setpoint value to be written.

**Raises:**

- `requests.exceptions.HTTPError`: If the API call fails.

### `write_schedule(schedule: Dict[str, Any])`

Writes a new schedule for devices via the Core API.

This function sends a POST request to the `/devices/schedule/{MPC_PRIORITY}` endpoint to submit a new operational schedule for one or more devices. The schedule is assigned a priority level defined by `MPC_PRIORITY`.

**Args:**

- `schedule`: A dictionary representing the schedule to be written. The structure of this dictionary is defined by the Core API.

**Raises:**

- `requests.exceptions.HTTPError`: If the API call fails.