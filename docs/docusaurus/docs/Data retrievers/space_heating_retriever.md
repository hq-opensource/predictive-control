---
sidebar_position: 5
---

# Space Heating Data Retriever

This module defines the `SpaceHeatingDataRetriever` class for fetching space heating device data.

It extends the abstract `DeviceRetriever` class, providing a concrete implementation for retrieving both static parameters and dynamic (time-series) data relevant to space heating systems (e.g., smart thermostats). This includes fetching initial indoor temperatures, setpoint preferences, occupancy preferences, and weather forecasts from the Core API. It also integrates with the thermal model learning component to ensure the MPC has accurate thermal dynamics.

## Classes

### `SpaceHeatingDataRetriever`

A concrete implementation of `DeviceRetriever` for space heating devices (smart thermostats).

This class specializes in retrieving both static parameters and dynamic (time-series) data relevant to space heating systems. It defines the default properties for space heating zones and fetches their initial temperature, setpoint preferences, occupancy preferences, and weather forecasts from the Core API. It also incorporates a thermal model learning component.

#### Methods

##### `_get_static_properties() -> Dict[str, Dict[str, Any]]`

Defines the static properties specific to space heating devices.

##### `_load_dynamic_data(start: datetime, stop: datetime) -> Dict[str, Any]`

Loads dynamic (time-series) data for space heating devices. This method fetches the initial temperature, setpoint preferences, and occupancy preferences for each space heating device from the Core API over the specified time range. It also retrieves the temperature forecast and triggers the learning of the thermal model.