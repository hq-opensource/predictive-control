---
sidebar_position: 2
---

# Device Retriever

This module defines the abstract base class for all device-specific data retrievers.

It establishes a common interface (`DeviceRetriever`) for fetching both static properties and dynamic (time-series) data relevant to various controllable devices. Subclasses of `DeviceRetriever` are responsible for implementing the logic to retrieve data specific to their device types, ensuring that the Model Predictive Control (MPC) system has access to all necessary inputs for its optimization.

## Classes

### `DeviceRetriever`

Abstract base class for retrieving data related to devices.

This class defines a common interface for fetching both static properties and dynamic (time-series) data for various devices. Subclasses must implement methods to define their specific static properties and how to load their dynamic data.

#### Methods

##### `__init__(devices: List[Dict[str, Any]])`

Initializes the `DeviceRetriever` with a list of device configurations.

##### `retrieve_data(start: datetime, stop: datetime) -> Dict[str, Any]`

Retrieves all necessary data (static and dynamic) for the devices.

This method orchestrates the data retrieval process. It first gathers static properties for each device and then loads dynamic time-series data for the specified time range.

##### `_load_dynamic_data(start: datetime, stop: datetime) -> Dict[str, Any]`

Abstract method to load dynamic (time-series) data for the devices. Subclasses must implement this method.

##### `_get_static_properties() -> Dict[str, Dict[str, Any]]`

Abstract method to define the static properties of the devices. Subclasses must implement this method.