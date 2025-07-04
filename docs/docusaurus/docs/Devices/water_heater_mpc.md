---
sidebar_position: 7
---

# Water Heater MPC

This module defines the `WaterHeaterMPC` class, which models an electric water heater for MPC.

It extends the abstract `DeviceMPC` class, providing a concrete implementation for formulating the optimization problem specific to controlling a water heater. This includes defining objectives related to maintaining water temperature within a desired range and incorporating constraints such as power limits, tank volume, and thermal dynamics influenced by ambient temperature and water flow.

## Classes

### `WaterHeaterMPC`

Represents a water heater for the MPC.

This class models the thermal behavior of an electric water heater. It formulates an optimization problem to control the heater's power consumption to maintain the water temperature within a desired range, while considering hot water usage, heat losses, and system constraints.

#### Methods

##### `__init__(devices: List[Dict[str, Any]])`

Initializes the `WaterHeaterMPC`.

**Args:**

- `devices`: A list of dictionaries, where each dictionary contains the configuration and parameters of a water heater device.

##### `create_mpc_formulation(start: datetime, stop: datetime, steps_horizon_k: int, interval: int = 10, norm_factor: int = 50)`

Creates the optimization formulation for the water heater.

This method constructs a CVXPY optimization problem based on a thermal model of the water heater tank. The objective is to minimize deviations from a desired temperature setpoint. The model includes constraints for:
- The thermal dynamics of the water tank, accounting for heating, heat loss to the ambient environment, and hot water draws.
- Temperature limits (min and max).
- Maximum power output of the heating element.

**Args:**

- `start`: The start time of the optimization horizon.
- `stop`: The end time of the optimization horizon.
- `steps_horizon_k`: The number of time steps in the horizon.
- `interval`: The duration of each time step in minutes.
- `norm_factor`: A normalization factor for the objective function.

**Returns:**

- A tuple containing the objective terms, constraints, and the dispatch variable for the CVXPY optimization problem.