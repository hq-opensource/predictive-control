---
sidebar_position: 6
---

# Water Heater Data Retriever

This module defines the `WaterHeaterDataRetriever` class for fetching water heater device data.

It extends the abstract `DeviceRetriever` class, providing a concrete implementation for retrieving both static parameters and dynamic (time-series) data relevant to electric water heaters. This includes fetching initial water temperature, hot water consumption preferences, and ambient temperature from the Core API, which are essential inputs for the water heater MPC model.

## Classes

### `WaterHeaterDataRetriever`

A concrete implementation of `DeviceRetriever` for water heater devices.

This class specializes in retrieving both static parameters and dynamic (time-series) data relevant to electric water heaters. It defines the default properties for water heaters and fetches their initial temperature, hot water consumption preferences, and ambient temperature from the Core API.

#### Methods

##### `_get_static_properties() -> Dict[str, Dict[str, Any]]`

Defines the static properties specific to water heater devices.

##### `_load_dynamic_data(start: datetime, stop: datetime) -> Dict[str, Any]`

Loads dynamic (time-series) data for water heater devices. This method fetches the initial water temperature, hot water consumption preferences, and ambient temperature for each water heater from the Core API over the specified time range. It also handles cases where a thermal zone might not be associated with a water heater.