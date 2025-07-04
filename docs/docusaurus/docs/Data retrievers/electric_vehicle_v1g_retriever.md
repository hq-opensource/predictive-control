---
sidebar_position: 4
---

# Electric Vehicle V1G Data Retriever

This module defines the `ElectricVehicleV1gDataRetriever` class for fetching V1G electric vehicle data.

It extends the abstract `DeviceRetriever` class, providing a concrete implementation for retrieving both static parameters and dynamic (time-series) data relevant to unidirectional electric vehicle charging. This includes fetching initial state of charge (SoC), SoC preference profiles, and branched (connection) profiles from the Core API, which are essential inputs for the electric vehicle MPC model.

## Classes

### `ElectricVehicleV1gDataRetriever`

A concrete implementation of `DeviceRetriever` for V1G electric vehicles.

This class specializes in retrieving both static parameters and dynamic (time-series) data relevant to unidirectional electric vehicle charging. It defines the default properties for V1G EVs and fetches their initial state of charge, SoC preferences, and branched (connection) profiles from the Core API.

#### Methods

##### `_get_static_properties() -> Dict[str, Dict[str, Any]]`

Defines the static properties specific to V1G electric vehicles.

##### `_load_dynamic_data(start: datetime, stop: datetime) -> Dict[str, Any]`

Loads dynamic (time-series) data for V1G electric vehicles. This method fetches the initial state of charge (SoC), SoC preference profiles, and branched (connection) profiles for each electric vehicle from the Core API over the specified time range.