---
sidebar_position: 2
---

# Thermal Models

This class provides the optimization models used to execute the learning of the thermal models.

This class encapsulates the mathematical formulation for learning the parameters of a thermal dynamics model (e.g., a black-box state-space model) from historical data. It uses CVXPY to define and solve the optimization problem.

## Classes

### `ThermalModels`

Provides the optimization models used to execute the learning of the thermal models.

#### Methods

##### `__init__()`

Initializes the `ThermalModels` class. Currently, it does not take any inputs.

##### `learn_black_model(x_internal_states: np.ndarray, u_heaters: np.ndarray, w_external_variables: np.ndarray, learning_weigths: List = [1, 1, 1], verbose: bool = False) -> Dict[str, Any] | None`

Learns the thermal dynamics of residential houses using a black-box model.

This method formulates and solves an optimization problem to identify the parameters (Ax, Au, Aw matrices) of a linear state-space thermal model: `Y_estimated = Ax * X + Au * U + Aw * W`.

The objective is to minimize the squared error between the estimated and measured internal states (temperatures), with regularization terms on the model parameters to prevent overfitting. Constraints are applied to ensure physical realism and model stability.

**Args:**

- `x_internal_states`: A NumPy array representing the historical internal states (e.g., indoor temperatures).
- `u_heaters`: A NumPy array representing the historical control inputs (e.g., heater power consumption).
- `w_external_variables`: A NumPy array representing the historical external variables (e.g., outdoor temperature).
- `learning_weigths`: A list of three floats [lx, lu, lw] for the regularization terms in the objective.
- `verbose`: If True, the solver's output will be printed.

**Returns:**

- A dictionary containing the learned 'Ax', 'Au', and 'Aw' matrices as lists, or `None` if the optimization problem fails to solve or dimensions do not match.