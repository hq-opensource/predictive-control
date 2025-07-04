---
sidebar_position: 3
---

# Electric Storage MPC

This module defines the `ElectricStorageMPC` class, which models an electric battery storage system for MPC.

It extends the abstract `DeviceMPC` class, providing a concrete implementation for formulating the optimization problem specific to battery charging and discharging. This includes defining objectives related to maintaining a desired state of charge and incorporating constraints such as power limits and energy balance equations.

## Classes

### `ElectricStorageMPC`

Represents an electric storage device (e.g., a battery) for the MPC.

This class models the behavior of a stationary battery energy storage system (BESS). It formulates the optimization problem for charging and discharging the battery to meet certain objectives (e.g., maintaining a desired state of charge) while respecting the physical limitations of the device.

#### Methods

##### `__init__(devices: List[Dict[str, Any]])`

Initializes the `ElectricStorageMPC`.

**Args:**

- `devices`: A list of dictionaries, where each dictionary contains the configuration and parameters of an electric storage device.

##### `create_mpc_formulation(start: datetime, stop: datetime, steps_horizon_k: int, interval: int = 10, norm_factor: int = 10)`

Creates the optimization formulation for the electric storage device.

This method builds a CVXPY optimization problem that models the battery's behavior over the prediction horizon. The objective is to minimize the deviation from a desired state of charge, while adhering to constraints such as:
- State of charge (SoC) limits (min and max).
- Charging and discharging power limits.
- The energy balance equation that governs how SoC changes over time.

**Args:**

- `start`: The start time of the optimization horizon.
- `stop`: The end time of the optimization horizon.
- `steps_horizon_k`: The number of time steps in the horizon.
- `interval`: The duration of each time step in minutes.
- `norm_factor`: A normalization factor for the objective function.

**Returns:**

- A tuple containing the objective terms, constraints, and the dispatch variable for the CVXPY optimization problem.