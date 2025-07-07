---
sidebar_position: 6
---

# Space Heating

Space heating, implemented as a smart thermostat, is a key component of residential energy systems, especially in cold climates where heating needs contribute significantly to Demand Response (DR). The Model Predictive Control (MPC) formulation for heating optimizes the temperature in multiple thermal zones of a dwelling, ensuring occupant comfort while respecting grid power constraints. This section presents the heating MPC formulation, which considers thermal dynamics, occupancy schedules, and external disturbances such as weather conditions. By prioritizing occupied zones and limiting power peaks, the formulation enhances DR and integrates seamlessly with Home Energy Management Systems (HEMS).

The formulation relies on a multi-zone thermal model that captures the interactions between heat inputs, internal temperatures, and external factors like outdoor temperature and solar radiation. The objective combines a comfort penalty for temperature deviations and a penalty for the maximum deviation in occupied zones, weighted by user-defined priorities and occupancy status. The use of a linear thermal model and continuous power control ensures computational efficiency, making this approach suitable for real-time optimization on embedded devices. This approach was chosen to balance thermal model precision and feasibility of large-scale implementation in a residential context.

### Optimization Formulation

The heating MPC formulation optimizes the power allocated to baseboard heaters across $Z$ thermal zones over a prediction horizon $T$, with time steps of duration $\Delta t$ (e.g., 10 minutes). The objective minimizes a combination of the squared temperature deviations across all zones and the maximum absolute deviation in occupied zones, both weighted by priorities and occupancy status. The power allocation cost is included in the overall MPC objective, while the comfort term is specific to heating.

The comfort penalty is formulated as follows:
```latex
J_{SH,k} = \sum_{z=1}^{Z} \sum_{k=1}^{T} P_{SH,z} O_{SH,z,k} \left( \frac{X^{d}_{SH,z,k} - X_{SH,z,k}}{\Delta \alpha_{SH}} \right)^2 + 100 \max_{z,k} \left( P_{SH,z} O_{SH,z,k} \left| \frac{X^{d}_{SH,z,k} - X_{SH,z,k}}{\Delta \alpha_{SH}} \right| \right)
```
where:
- $ P_{SH,z} $ is the priority weight for thermal zone $ z $.
- $ O_{SH,z,k} $ is the occupancy status (0 or 1) for zone $ z $ at time $ k $.
- $ X^{d}_{SH,z,k} $ is the desired temperature (setpoint) for zone $ z $ at time $ k $.
- $ X_{SH,z,k} $ is the actual temperature of zone $ z $ at time $ k $.
- $ \Delta \alpha_{SH} $ is the normalization factor (e.g., 10°C, generally the interval between minimum and maximum setpoints).

The thermal dynamics of heating across all zones are modeled by:
```latex
X^{SH}_{k+1} = A_x X^{SH}_{k} + A_u S^{SH}_{k+1} + A_w W_{k+1}, \quad \forall k
```
where:
- $ X^{SH}_{k} $ is the state vector of temperatures in all $ Z $ zones at time $ k $.
- $ S^{SH}_{k} $ is the heating power vector applied to $ U $ heaters at time $ k $.
- $ W_{k} $ is the vector of external disturbances (e.g., outdoor temperature, solar radiation) at time $ k $.
- $A_x$, $A_u$, $A_w$ are matrices representing the thermal model for internal states, heating inputs, and external disturbances, respectively.

Constraints ensure that heating operates within physical and operational limits:
- **Temperature Limits**:
```latex
\underline{X}^{SH}_z \leq X_{SH,z,k} \leq \overline{X}^{SH}_z, \quad \forall z, k
```
where $ \underline{X}^{SH}_z $ and $ \overline{X}^{SH}_z $ are the minimum and maximum temperature setpoints for zone $ z $.
- **Power Limits**:
```latex
0 \leq S^{SH}_{u,k} \leq \frac{16.0}{U}, \quad \forall u, k
```
where $ S^{SH}_{u,k} $ is the power of baseboard heater $ u $ at time $ k $, and $ U $ is the total number of baseboard heaters, with a global limit of 16 kW distributed equally. 16 kW limit set for an average house in Quebec.
- **Power Variation Constraints**:
```latex
| S^{SH}_{u,k} - S^{SH}_{u,k-1} | \leq 2.0, \quad \forall u, k \geq 1
```
to limit abrupt variations for operational stability.
- **Initial Condition**:
```latex
X^{SH}_{0} = X^{SH}_{\text{initial}}
```
where $ X^{SH}_{\text{initial}} $ is the initial temperature vector for all zones.

The power allocation for heating, which contributes to the global power constraint, is given by:
```latex
S^{SH}_{k} = \sum_{u=1}^{U} S^{SH}_{u,k}, \quad \forall k
```

### Justification of the Formulation

The heating formulation prioritizes occupant comfort by minimizing temperature deviations in occupied zones, with an additional penalty on the maximum deviation to ensure critical zones remain within acceptable limits. The use of occupancy status ($ O_{SH,z,k} $) allows the controller to focus energy allocation on occupied zones, improving efficiency during DR events. The multi-zone thermal model, with matrices $A_x$, $A_u$, $A_w$, captures complex interactions between zones and external conditions, ensuring accurate predictions. The constraint on power variation limits rapid fluctuations, protecting equipment and ensuring grid stability. Continuous power control and linear dynamics enable efficient optimization, making the formulation suitable for real-time applications on embedded devices. The fixed power limit per baseboard heater (16 kW divided by the number of baseboard heaters) reflects the characteristics of an average Quebec house, while dynamic setpoints allow flexible user customization.

### Variable Definitions

Variables and parameters specific to the heating formulation are summarized in the following table.

| Variable/Parameter | Description | Units |
|---|---|---|
| $ S^{SH}_{u,k} $ | Power allocated to heater $ u $ at time $ k $ | kW |
| $ S^{SH}_{k} $ | Total power allocated to heating at time $ k $ | kW |
| $ X_{SH,z,k} $ | Temperature of thermal zone $ z $ at time $ k $ | °C |
| $ X^{d}_{SH,z,k} $ | Desired temperature (setpoint) for zone $ z $ at time $ k $ | °C |
| $ P_{SH,z} $ | Priority weight for thermal zone $ z $ | - |
| $ O_{SH,z,k} $ | Occupancy status (0 or 1) for zone $ z $ at time $ k $ | - |
| $ \Delta \alpha_{SH} $ | Normalization factor (e.g., 10°C) | °C |
| $ A_x $ | Thermal model matrix for internal states | - |
| $ A_u $ | Thermal model matrix for heating inputs | - |
| $ A_w $ | Thermal model matrix for external disturbances | - |
| $ W_{k} $ | Vector of external disturbances (e.g., outdoor temperature) at time $ k $ | Variable |
| $ \underline{X}^{SH}_z $ | Minimum temperature setpoint for zone $ z $ | °C |
| $ \overline{X}^{SH}_z $ | Maximum temperature setpoint for zone $ z $ | °C |
| $ X^{SH}_{\text{initial}} $ | Initial temperature vector for all zones | °C |
| $ Z $ | Number of thermal zones | - |
| $ U $ | Number of heaters | - |


## Classes
This module defines the `SpaceHeatingMPC` class, which models a space heating system for MPC.

It extends the abstract `DeviceMPC` class, providing a concrete implementation for formulating the optimization problem specific to controlling electric heaters in thermal zones. This includes defining objectives related to maintaining indoor temperature within comfort bounds and incorporating constraints such as heater power limits and thermal dynamics based on a state-space model.
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
