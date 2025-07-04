---
sidebar_position: 2
---

# Executor MPC

This module defines the `ExecutorMPC` class, which orchestrates the Model Predictive Control (MPC) process.

It serves as the primary interface for initiating and running an MPC optimization cycle.
The `ExecutorMPC` is responsible for:
- Initializing the global MPC problem builder (`BuildGlobalMPC`).
- Constructing the comprehensive optimization problem based on selected device types.
- Solving the formulated MPC problem to determine optimal control actions.
- Returning the solved problem and the resulting net grid power exchange.

## Classes

### `ExecutorMPC`

Orchestrates the execution of the Model Predictive Control (MPC) process.

This class is responsible for initializing the global MPC problem builder, constructing the optimization problem based on specified device types, solving the problem, and returning the results. It acts as the main entry point for running an MPC optimization cycle.

#### Methods

##### `__init__(space_heating: bool, electric_storage: bool, electric_vehicle: bool, water_heater: bool)`

Initializes the `ExecutorMPC` with flags indicating which device types to include.

**Args:**

- `space_heating`: A boolean indicating whether to include space heating devices.
- `electric_storage`: A boolean indicating whether to include electric storage devices.
- `electric_vehicle`: A boolean indicating whether to include electric vehicle devices.
- `water_heater`: A boolean indicating whether to include water heater devices.

##### `run_mpc(start: datetime, stop: datetime, interval: int, price_profile: Dict[datetime, float], power_limit: Dict[datetime, float]) -> Tuple[cvx.Problem, cvx.Expression]`

Executes a full MPC optimization cycle.

This method first calls the `create_mpc_formulation` method of the `BuildGlobalMPC` instance to construct the optimization problem. Then, it calls the `solve_mpc` method to find the optimal solution.

**Args:**

- `start`: The start time of the optimization horizon.
- `stop`: The end time of the optimization horizon.
- `interval`: The time step interval in minutes for the optimization horizon.
- `price_profile`: A dictionary mapping timestamps to electricity prices over the horizon.
- `power_limit`: A dictionary mapping timestamps to the maximum allowable grid power exchange.

**Returns:**

- A tuple containing:
  - The solved CVXPY Problem object.
  - A CVXPY Expression representing the net grid power exchange, which is the sum of all device dispatches and non-controllable loads.