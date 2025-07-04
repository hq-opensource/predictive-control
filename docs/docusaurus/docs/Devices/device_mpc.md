---
sidebar_position: 2
---

# Device MPC

This module defines the abstract base class for all devices integrated into the MPC system.

It establishes a common interface (`DeviceMPC`) that each controllable device must implement. This interface ensures that every device can provide its specific optimization formulation, including objective terms, constraints, and dispatch variables, allowing them to be seamlessly incorporated into a larger, aggregated Model Predictive Control problem.

## Classes

### `DeviceMPC`

Abstract base class for a device compatible with the Model Predictive Control (MPC).

This class defines the interface that all controllable devices must implement to be included in the MPC optimization. It ensures that every device can provide its own set of objectives and constraints to the central optimization problem.

#### Methods

##### `create_mpc_formulation(start: datetime, stop: datetime, steps_horizon_k: int, interval: int = 10, norm_factor: int = 10)`

Creates the optimization formulation for the device.

This method is responsible for defining the mathematical model of the device's behavior, including its operational constraints and its contribution to the overall optimization objective (e.g., minimizing energy cost, maximizing comfort).

**Args:**

- `start`: The start time of the optimization horizon.
- `stop`: The end time of the optimization horizon.
- `steps_horizon_k`: The number of time steps in the optimization horizon.
- `interval`: The duration of each time step in minutes.
- `norm_factor`: A normalization factor used in the objective function to balance different physical units and magnitudes.

**Returns:**

- A tuple containing three elements:
  - A list of objective terms (cvxpy expressions) that the MPC will seek to minimize.
  - A list of constraints (cvxpy constraints) that model the device's physical and operational limitations.
  - A `cvxpy.Variable` representing the device's power dispatch over the horizon. This variable links the device's behavior to the building's total consumption.