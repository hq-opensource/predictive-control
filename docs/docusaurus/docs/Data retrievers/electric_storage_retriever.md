---
sidebar_position: 3
---

# Electric Storage Data Retriever

This module defines the `ElectricStorageDataRetriever` class for fetching electric storage device data.

It extends the abstract `DeviceRetriever` class, providing a concrete implementation for retrieving both static parameters and dynamic (time-series) data relevant to electric battery storage systems. This includes fetching initial state of charge (SoC) and SoC preference profiles from the Core API, which are crucial inputs for the electric storage MPC model.

## Classes

### `ElectricStorageDataRetriever`

A concrete implementation of `DeviceRetriever` for electric storage devices.

This class specializes in retrieving both static parameters and dynamic (time-series) data relevant to electric battery storage systems. It defines the default properties for electric storage and fetches their initial state of charge and SoC preferences from the Core API.

#### Methods

##### `_get_static_properties() -> Dict[str, Dict[str, Any]]`

Defines the static properties specific to electric storage devices.

##### `_load_dynamic_data(start: datetime, stop: datetime) -> Dict[str, Any]`

Loads dynamic (time-series) data for electric storage devices. This method fetches the initial state of charge (SoC) for each electric storage device and their SoC preference profiles over the specified time range from the Core API.