---
sidebar_position: 6
---

# Space Heating MPC

This module defines the `SpaceHeatingMPC` class, which models a space heating system for MPC.

It extends the abstract `DeviceMPC` class, providing a concrete implementation for formulating the optimization problem specific to controlling electric heaters in thermal zones. This includes defining objectives related to maintaining indoor temperature within comfort bounds and incorporating constraints such as heater power limits and thermal dynamics based on a state-space model.

## Classes

### `SpaceHeatingMPC`

Represents a space heating system (e.g., smart thermostats) for the MPC.

This class models the thermal behavior of one or more building zones controlled by electric heaters. It uses a state-space thermal model to predict temperature evolution and formulates an optimization problem to control the heaters' power output. The goal is to maintain the indoor temperature close to the desired setpoints while respecting comfort boundaries and system constraints.

#### Methods

##### `__init__(devices: List[Dict[str, Any]])`

Initializes the `SpaceHeatingMPC`.

**Args:**

- `devices`: A list of dictionaries, where each dictionary contains the configuration and parameters of a space heating device (thermal zone).

##### `create_mpc_formulation(start: datetime, stop: datetime, steps_horizon_k: int, interval: int = 10, norm_factor: int = 10)`

Creates the optimization formulation for the space heating system.

This method constructs a CVXPY optimization problem based on a linear state-space model of the building's thermal dynamics. The objective function penalizes deviations from temperature setpoints, weighted by occupancy and user-defined priorities. The constraints include:
- The state-space thermal balance equation.
- Temperature comfort bounds (min and max setpoints).
- Maximum power output of the heaters.
- Ramping limits on heater power to prevent rapid cycling.

**Args:**

- `start`: The start time of the optimization horizon.
- `stop`: The end time of the optimization horizon.
- `steps_horizon_k`: The number of time steps in the horizon.
- `interval`: The duration of each time step in minutes.
- `norm_factor`: A normalization factor for the objective function.

**Returns:**

- A tuple containing the objective terms, constraints, and the dispatch variable for the CVXPY optimization problem.