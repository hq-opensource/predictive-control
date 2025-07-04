---
sidebar_position: 1
---

# API Calls

This module provides a collection of API client functions for retrieving various types of data.

It serves as a centralized interface for fetching device information, device states, building consumption data, user preferences, historical data, and weather forecasts from the Core API. These functions are essential for gathering the necessary inputs for the Model Predictive Control (MPC) system.

## Functions

### `get_devices()`
Retrieves the installed devices from the Core API.

### `get_device_state(device_id: str, field: str | None = None)`
Retrieves the state of a specific device from the Core API.

### `retrieve_total_consumption()`
Retrieves the real-time total consumption of the building from the Core API.

### `get_preferences_data(preferences_type: str, device_id: str, start: datetime, stop: datetime)`
Retrieves preferences data for a specified type and device over a time range from the Core API.

### `get_historical_data(historic_type: str, start: datetime, stop: datetime, device_id: Optional[str] = None)`
Retrieves historical data for a specified type over a time range from the Core API.

### `get_weather_historic(variable: str, start: datetime, stop: datetime)`
Retrieves historic weather data from the Core API's weather endpoint.

### `get_weather_forecast(variable: str, start: datetime, stop: datetime)`
Retrieves weather forecast data from the Core API's weather endpoint.

### `get_non_controllable_loads_forecast(variable: str, start: datetime, stop: datetime)`
Retrieves the forecast for non-controllable loads from the Core API.

### `write_setpoint(device_id: str, setpoint: float)`
Writes a new setpoint for a specific device via the Core API.