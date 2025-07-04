---
sidebar_position: 3
---

# Interpreter

This module defines the `Interpreter` class, responsible for processing and persisting MPC optimization results.

It extracts optimal variable values from the solved CVXPY problem, transforms them into structured data (e.g., Pandas DataFrames), and handles their storage in a time-series database like InfluxDB. The Interpreter ensures that the complex outputs of the MPC solver are converted into actionable and storable insights, providing a clear view of the system's optimized behavior and control signals.

## Classes

### `Interpreter`

Interprets and processes the results of the CVXPY Model Predictive Control (MPC) optimization problem.

This class is responsible for extracting optimal variable values from the solved CVXPY problem, transforming them into meaningful data structures (e.g., Pandas DataFrames), and persisting these results to a time-series database like InfluxDB. It handles device-specific result interpretation and data formatting.

#### Methods

##### `__init__(start: datetime, stop: datetime)`

Initializes the Interpreter with the start and stop times of the optimization horizon.

**Args:**

- `start`: The start datetime of the optimization horizon.
- `stop`: The end datetime of the optimization horizon.

##### `interpret(global_mpc_problem: Problem, space_heating: bool, electric_storage: bool, electric_vehicle: bool, water_heater: bool) -> pd.DataFrame`

Interprets the results of the global MPC problem and saves them.

This is the main method for processing the optimization output. It iterates through the enabled device types, extracts their respective control and state variables from the solved `global_mpc_problem`, converts them into Pandas DataFrames, and then saves these results to InfluxDB. It also aggregates the control signals into a single DataFrame.

**Args:**

- `global_mpc_problem`: The solved CVXPY Problem object.
- `space_heating`: A boolean indicating if space heating devices were included.
- `electric_storage`: A boolean indicating if electric storage devices were included.
- `electric_vehicle`: A boolean indicating if electric vehicle devices were included.
- `water_heater`: A boolean indicating if water heater devices were included.

**Returns:**

- A Pandas DataFrame containing the aggregated control signals for all controllable devices over the optimization horizon.

##### `load_water_heater_variables(global_mpc_problem: Problem, devices: List[Dict[str, Any]], interval: int = 10) -> Tuple[pd.DataFrame, pd.DataFrame]`

Extracts and processes water heater variables from the solved MPC problem.

This method retrieves the optimal power dispatch and temperature profiles for the water heater from the `global_mpc_problem`'s variables. It then formats these into Pandas DataFrames for further use and storage.

**Args:**

- `global_mpc_problem`: The solved CVXPY Problem object.
- `devices`: A list of device dictionaries, used to retrieve entity IDs.
- `interval`: The time step interval in minutes.

**Returns:**

- A tuple containing two Pandas DataFrames:
  - `results_water_heater`: Contains the raw power and temperature profiles.
  - `control_water_heater`: Contains the control signals (power) mapped to device entity IDs.

##### `load_electric_storage_variables(global_mpc_problem: Problem, devices: List[Dict[str, Any]], interval: int = 10) -> Tuple[pd.DataFrame, pd.DataFrame]`

Extracts and processes electric storage variables from the solved MPC problem.

This method retrieves the optimal charge/discharge power, residual energy, and state of charge (SoC) for the electric storage device from the `global_mpc_problem`'s variables. It then formats these into Pandas DataFrames.

**Args:**

- `global_mpc_problem`: The solved CVXPY Problem object.
- `devices`: A list of device dictionaries, used to retrieve device parameters.
- `interval`: The time step interval in minutes.

**Returns:**

- A tuple containing two Pandas DataFrames:
  - `results_electric_storage`: Contains the raw charge/discharge power, residual energy, net power, and SoC profiles.
  - `control_electric_storage`: Contains the net power control signals mapped to device entity IDs.

##### `load_space_heating_variables(global_mpc_problem: Problem, devices: List[Dict[str, Any]], interval: int = 10) -> Tuple[pd.DataFrame, pd.DataFrame]`

Extracts and processes space heating variables from the solved MPC problem.

This method retrieves the optimal heater power dispatch and indoor temperature profiles for each thermal zone from the `global_mpc_problem`'s variables. It then formats these into Pandas DataFrames.

**Args:**

- `global_mpc_problem`: The solved CVXPY Problem object.
- `devices`: A list of device dictionaries, used to order thermal zones.
- `interval`: The time step interval in minutes.

**Returns:**

- A tuple containing two Pandas DataFrames:
  - `results_space_heating`: Contains the raw heater power and temperature profiles.
  - `control_space_heating`: Contains the temperature setpoint control signals mapped to thermal zone entity IDs.