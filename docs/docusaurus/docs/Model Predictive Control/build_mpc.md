---
sidebar_position: 1
---

# Build Global MPC

This module defines the `BuildGlobalMPC` class, responsible for constructing and solving the overall MPC problem.

It integrates individual device-specific MPC formulations (from modules like `electric_storage_mpc`, `space_heating_mpc`, etc.) into a single, comprehensive optimization problem. This module handles the aggregation of objectives and constraints from various controllable devices, incorporates global factors like electricity prices and grid power limits, and manages the execution of the CVXPY solver to determine optimal dispatch strategies.

## Classes

### `BuildGlobalMPC`

Manages the construction and solution of the overall Model Predictive Control (MPC) problem.

This class aggregates the individual MPC formulations from various controllable devices (e.g., electric storage, space heating, electric vehicles, water heaters) into a single, comprehensive optimization problem. It also incorporates global constraints such as electricity prices and grid power limits.

#### Methods

##### `__init__(space_heating: bool, electric_storage: bool, electric_vehicle: bool, water_heater: bool)`

Initializes the `BuildGlobalMPC` with flags indicating which device types to include.

**Args:**

- `space_heating`: A boolean indicating whether to include space heating devices.
- `electric_storage`: A boolean indicating whether to include electric storage devices.
- `electric_vehicle`: A boolean indicating whether to include electric vehicle devices.
- `water_heater`: A boolean indicating whether to include water heater devices.

##### `solve_mpc(global_mpc_problem: cvx.Problem) -> cvx.Problem`

Solves the constructed global MPC problem.

This method takes a CVXPY Problem object, solves it using the SCS solver, and logs the execution time and problem status.

**Args:**

- `global_mpc_problem`: The CVXPY Problem object representing the aggregated MPC.

**Returns:**

- The solved CVXPY Problem object, containing the optimal variable values.

##### `create_mpc_formulation(start: datetime, stop: datetime, interval: int, price_profile: Dict[datetime, float], power_limit: Dict[datetime, float]) -> Tuple[cvx.Problem, cvx.Expression]`

Creates the full MPC formulation by aggregating all enabled devices.

This method orchestrates the creation of the overall optimization problem. It retrieves forecasts for non-controllable loads, validates input data, and then iteratively calls the `create_mpc_formulation` method for each instantiated device to gather their objectives and constraints. Finally, it combines these with the global objective (minimizing energy cost) and constraints (e.g., grid power limits) to form the complete CVXPY problem.

**Args:**

- `start`: The start time of the optimization horizon.
- `stop`: The end time of the optimization horizon.
- `interval`: The time step interval in minutes for the optimization horizon.
- `price_profile`: A dictionary mapping timestamps to electricity prices over the horizon.
- `power_limit`: A dictionary mapping timestamps to the maximum allowable grid power exchange.

**Returns:**

- A tuple containing:
  - The constructed CVXPY Problem object.
  - A CVXPY Expression representing the net grid power exchange, which is the sum of all device dispatches and non-controllable loads.

**Raises:**

- `ValueError`: If the stop time is not greater than the start time.