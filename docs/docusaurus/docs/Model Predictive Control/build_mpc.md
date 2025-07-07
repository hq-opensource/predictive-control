---
sidebar_position: 1
---

# Model Predictive Control

The global optimization formulation of the Model Predictive Control (MPC) strategy for Demand Response (DR) integrates the individual control strategies of residential equipment: electric storage, water heaters, space heaters, and electric vehicles. By aggregating objectives and constraints at the equipment level, the global MPC ensures that total energy consumption is maintained within limits imposed by the electricity provider, while optimizing energy costs and user comfort. This approach enables robust and scalable energy management, suitable for integration with Home Energy Management Systems (HEMS).

The global MPC formulation minimizes a composite objective that combines the cost of energy consumption (based on dynamic electricity tariffs) with equipment-specific comfort penalties. It imposes a power limitation constraint to prevent demand peaks, ensuring grid stability when service is restored. The use of a convex optimization framework, solved using the Splitting Conic Solver (SCS), ensures computational efficiency suitable for real-time applications on embedded devices. The flexibility of the formulation, which allows for the creation of necessary equipment, makes it adaptable to a wide variety of residential configurations, thereby enhancing its practical applicability.

### Optimization Formulation

The global MPC optimizes power allocation among a set of controllable equipment $W$ over a prediction horizon $T$, with time steps of duration $\Delta t$ (e.g., 10 minutes). The objective minimizes the total cost, including energy cost based on dynamic tariffs and aggregated comfort penalties from all active equipment:
$$
\min \sum_{k=1}^{T} \left( \pi_k \left( \sum_{w \in W} S_{w,k} + S^U_k \right) + \sum_{w \in W} J_{w,k} \right)
$$
where:
- $ \pi_k $ is the dynamic electricity tariff at time $ k $ (in $/W).
- $ S_{w,k} $ is the power allocated to equipment $ w $ at time $ k $.
- $ S^U_k $ is the power consumed by uncontrollable loads at time $ k $, predicted via the Python Prophet library.
- $ J_{w,k} $ is the comfort penalty specific to equipment $ w $ at time $ k $, defined in the respective sections.

The net power exchange with the grid, representing the total power drawn, is given by:
$$
S^{\text{net}}_k = \sum_{w \in W} S_{w,k} + S^U_k, \quad \forall k
$$

Global constraints ensure that the system operates within its operational limits:
- **Power Limit Constraint**:
$$
S^{\text{net}}_k \leq S^L_k, \quad \forall k
$$
where $ S^L_k $ is the power limit imposed by the electricity provider at time $ k $ (in kilo-Watts).
- **Equipment-Specific Constraints**: For each equipment $ w \in W $, the constraints defined in the corresponding sections (e.g., state limits, dynamics, and power constraints) are included.

### Creation of Controllable Devices

The global MPC formulation is designed to be flexible, allowing the inclusion of any combination of supported equipment (electric storage, water heater, space heating, electric vehicle) via boolean indicators. The set of active equipment $W$ is dynamically determined based on these indicators, as follows:
- If the electric storage indicator is enabled, the MPC for storage is instantiated, contributing its objective $ J_{BS,k} $, constraints, and dispatch $ S^{BS}_k $.
- If the water heater indicator is enabled, the MPC for the water heater is instantiated, contributing $ J_{WH,k} $, its constraints, and its dispatch $ S^{WH}_k $.
- If the heating indicator is enabled, the MPC for heating is instantiated, contributing $ J_{SH,k} $, its constraints, and its dispatch $ S^{SH}_k $.
- If the electric vehicle indicator is enabled, the MPC for the electric vehicle is instantiated, contributing $ J_{EV,k} $, its constraints, and its dispatch $ S^{EV}_k $.
This modular approach ensures that the global MPC adapts to various household configurations, including only the equipment present in the system, which improves scalability and reduces computational load when few devices are active.

### Integration of External Data

The global MPC relies on external data to feed its predictions and constraints:
- **Uncontrollable Loads**: Consumption of uncontrollable loads ($ S^U_k $) is predicted using the Python Prophet library, which provides time-series forecasts based on historical data. The forecast is retrieved for the horizon from $ t_{\text{start}} $ to $ t_{\text{stop}} $, ensuring consistency with optimization steps.
- **Weather Forecasts**: Weather data, such as outdoor temperature and solar radiation, are obtained via the Tomorrow.io API for the external disturbance vector $ W_k $ of heating. These forecasts improve the accuracy of the thermal dynamics model.
- **Dynamic Pricing and Power Limits**: Electricity tariff $ \pi_k $ and power limit $ S^L_k $ are provided as time-varying inputs, aligned with provider signals, to optimize costs and ensure grid compliance.

### Justification of the Formulation

The global MPC formulation is designed to balance energy cost and user comfort during DR events. The composite objective function incorporates dynamic pricing to encourage economic energy allocation, while equipment-specific comfort penalties ensure that user preferences (e.g., desired temperatures, SoC levels) are respected. The power limitation constraint is essential for preventing demand peaks and protecting the grid when service is restored. The use of Prophet for uncontrollable load forecasting and Tomorrow.io for weather data enhances prediction accuracy, enabling proactive management of load variations. The flexible creation of existing controllable devices allows the MPC to adapt to diverse residential configurations, making it practical for large-scale deployment. The convex optimization framework, solved with the SCS solver, ensures computational efficiency, enabling real-time operation on embedded devices with relatively limited resources.

### Variable Definitions

Variables and parameters specific to the global optimization formulation are summarized in the following table. Equipment-specific variables are defined in their respective sections.

| Variable/Parameter | Description | Units |
|---|---|---|
| $ S_{w,k} $ | Power allocated to equipment $ w $ at time $ k $ | W |
| $ S^{\text{net}}_k $ | Net power exchange with the grid at time $ k $ | W |
| $ S^U_k $ | Power consumed by uncontrollable loads at time $ k $ | W |
| $ S^L_k $ | Power limit imposed by the electricity provider at time $ k $ | W |
| $ \pi_k $ | Dynamic electricity tariff at time $ k $ | $/W |
| $ J_{w,k} $ | Comfort penalty for equipment $ w $ at time $ k $ | - |
| $ W $ | Set of active controllable equipment | - |
| $ T $ | Prediction horizon | - |
| $ \Delta t $ | Time step duration | hours |


## Classes

This module defines the `BuildGlobalMPC` class, responsible for constructing and solving the overall MPC problem.

It integrates individual device-specific MPC formulations (from modules like `electric_storage_mpc`, `space_heating_mpc`, etc.) into a single, comprehensive optimization problem. This module handles the aggregation of objectives and constraints from various controllable devices, incorporates global factors like electricity prices and grid power limits, and manages the execution of the CVXPY solver to determine optimal dispatch strategies.


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
