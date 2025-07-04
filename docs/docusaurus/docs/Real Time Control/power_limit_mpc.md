---
sidebar_position: 1
---

# Power Limit MPC

This module implements the Real-Time Control (RTC) mechanism for enforcing power limits.

It defines the `RealTimeControl` class, which operates as a separate thread to continuously monitor the total building power consumption. When consumption exceeds a predefined dynamic power limit, the RTC applies curtailment actions to controllable devices based on their priorities and a debounce mechanism to prevent rapid cycling. This module is critical for ensuring that the building's power consumption adheres to grid constraints in real-time.

## Classes

### `RealTimeControl`

Implements a Real-Time Control (RTC) mechanism to enforce power limits.

This class operates as a separate thread, continuously monitoring the total building power consumption and comparing it against a dynamic power limit. If the consumption exceeds the limit, it applies curtailment actions to controllable devices based on their priorities and a debounce mechanism. It also includes logging and a placeholder for user notifications.

#### Methods

##### `__init__(power_limit: Dict[datetime, float], space_heating: bool, electric_storage: bool, electric_vehicle: bool, water_heater: bool)`

Initializes the `RealTimeControl` thread.

**Args:**

- `power_limit`: A dictionary mapping timestamps to the maximum allowable power consumption at those times.
- `space_heating`: A boolean indicating whether space heating devices are controllable.
- `electric_storage`: A boolean indicating whether electric storage devices are controllable.
- `electric_vehicle`: A boolean indicating whether electric vehicle devices are controllable.
- `water_heater`: A boolean indicating whether water heater devices are controllable.

##### `run()`

Main control loop for real-time power limit enforcement.

This method continuously monitors the total power consumption and, if necessary, applies curtailment actions to controllable devices. It prioritizes devices based on their configured priorities and respects a debounce time to prevent rapid cycling of controls. The loop runs as long as `self.must_run` is True.