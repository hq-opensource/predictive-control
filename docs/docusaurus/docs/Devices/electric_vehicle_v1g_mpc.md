---
sidebar_position: 4
---

# Electric Vehicle V1G MPC

This module defines the `ElectricVehicleV1GMPC` class, which models a V1G electric vehicle for MPC.

It extends the abstract `DeviceMPC` class, providing a concrete implementation for formulating the optimization problem specific to unidirectional electric vehicle charging. This includes defining objectives related to maintaining a desired state of charge and incorporating constraints such as charging power limits, battery capacity, and the vehicle's connection status.

## Classes

### `ElectricVehicleV1GMPC`

Represents a V1G (unidirectional charging) Electric Vehicle for the MPC.

This class models an electric vehicle that can only draw power from the grid (V1G - Vehicle-to-Grid unidirectional). It formulates an optimization problem to control the EV's charging schedule based on its availability (i.e., when it is plugged in) and charging preferences, while respecting the vehicle's battery constraints.

#### Methods

##### `__init__(device_info: List[Dict[str, Any]])`

Initializes the `ElectricVehicleV1GMPC`.

**Args:**

- `device_info`: A list containing a single dictionary with the configuration and parameters of the electric vehicle.

##### `create_mpc_formulation(start: datetime, stop: datetime, interval: int, v1g_info: Dict[str, pd.DataFrame])`

Creates the optimization formulation for the V1G electric vehicle.

This method builds a CVXPY optimization problem that determines the optimal charging schedule for the EV. The objective is to minimize the deviation from a desired state of charge. The model includes constraints for:
- SoC limits (min and max).
- Charging power limits.
- The EV's connection status (it can only charge when plugged in, as indicated by the `branched_profile`).
- The energy balance equation for the battery.

**Args:**

- `start`: The start time of the optimization horizon.
- `stop`: The end time of the optimization horizon.
- `interval`: The duration of each time step in minutes.
- `v1g_info`: A dictionary containing DataFrames for the 'initial_state' and 'branched_profile' (connection status) of the EV.

**Returns:**

- A tuple containing the objective terms, constraints, and the dispatch variable for the CVXPY optimization problem.

**Raises:**

- `ValueError`: If the input data (e.g., `branched_profile`, `initial_state`) has incorrect dimensions or values.