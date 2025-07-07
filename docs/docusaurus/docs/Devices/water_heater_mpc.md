---
sidebar_position: 7
---

# Water Heater

The water heater is an essential component in residential energy systems, especially in highly electrified homes where it significantly contributes to power demand during Demand Response (DR) events. The Model Predictive Control (MPC) formulation for the water heater optimizes its operation to maintain hot water availability while minimizing energy costs and respecting grid power limits. This section presents the MPC formulation for the water heater, which models the tank's temperature dynamics, considering heating power, heat losses to the ambient environment, and water consumption. The formulation prioritizes user comfort by minimizing deviations from a desired water temperature, making it suitable for integration into Home Energy Management Systems (HEMS).

The water heater operates with continuous power control, allowing flexible power allocation within the device's capacity limits, unlike binary on/off control. This approach enhances the MPC's ability to finely adjust energy usage, thereby reducing demand peaks during re-energization. The formulation is designed to be computationally efficient, using a linear model of temperature dynamics to ensure real-time optimization on embedded devices. The inclusion of water flow and ambient temperature effects allows for accurate modeling of real-world conditions, making the controller robust to varying usage profiles.

### Optimization Formulation

The MPC formulation for the water heater optimizes the power allocated to the device over a prediction horizon $T$, with time steps of duration $\Delta t$ (e.g., 10 minutes). The objective is to minimize the comfort penalty, defined as the squared deviation between the water temperature and a desired temperature, weighted by a user-defined priority. The power allocation cost is included in the overall MPC objective, while the comfort term is specific to the water heater.

The comfort penalty is formulated as follows:
```latex
J_{WH,k} = P_{WH} \sum_{k=1}^{T} \left( \frac{X^{d}_{WH} - X^{WH}_{k}}{\Delta \alpha_{WH}} \right)^2
```
where:
- $ P_{WH} $ is the priority weight for the water heater.
- $ X^{d}_{WH} $ is the desired water temperature (constant over the horizon, e.g., 80°C).
- $ X^{WH}_{k} $ is the water temperature at time $ k $.
- $ \Delta \alpha_{WH} $ is the normalization factor (e.g., 50 K).

The temperature dynamics of the water heater are modeled as follows:
```latex
X^{WH}_{k+1} = X^{WH}_{k} + \frac{\Delta t}{C V} \left[ S^{WH}_{k} - C \dot{V}_{k} (X^{WH}_{k} - X_{\text{inlet}}) - 2 (X^{WH}_{k} - T_a) \right], \quad \forall k
```
where:
- $ S^{WH}_{k} $ is the power allocated to the water heater at time $ k $.
- $ C $ is the water heater constant (thermal capacity per unit volume, in Wh/°C/L).
- $ V $ is the tank volume (in liters, converted to m³ for consistency).
- $ \dot{V}_{k} $ is the water flow rate at time $ k $ (in m³/s).
- $ X_{\text{inlet}} $ is the inlet water temperature (e.g., 16°C).
- $ T_a $ is the ambient temperature.
- $ \Delta t $ is the duration of the time step (in hours).

Constraints ensure that the water heater operates within physical and operational limits:
- **Temperature Limits**:
```latex
\underline{X}^{WH} \leq X^{WH}_{k} \leq \overline{X}^{WH}, \quad \forall k
```
where $ \underline{X}^{WH} $ and $ \overline{X}^{WH} $ are the minimum and maximum allowed temperatures (e.g., 30°C and 90°C).
- **Power Limits**:
```latex
0 \leq S^{WH}_{k} \leq S^{WH,\max}, \quad \forall k
```
where $ S^{WH,\max} $ is the maximum power of the water heater (in W).
- **Initial Condition**:
```latex
X^{WH}_{0} = X^{WH}_{\text{initial}}
```
where $ X^{WH}_{\text{initial}} $ is the initial water temperature.

The power injection of the water heater, which contributes to the global power constraint, is simply:
```latex
S^{WH}_{k}, \quad \forall k
```

### Justification of the Formulation

The continuous power formulation allows for finer granularity in power allocation, which is essential for mitigating DR peaks by avoiding abrupt power surges. The comfort penalty uses a constant desired temperature to simplify user input while ensuring hot water availability consistent with typical residential needs. The temperature dynamics model integrates water flow and thermal losses to the ambient environment, making it sensitive to actual usage patterns. The linearity of the dynamics and the absence of binary variables enhance computational efficiency, allowing MPC execution on resource-constrained embedded devices. The water heater constant $ C $ simplifies the thermal model by combining thermal capacity and conductance effects, reducing the number of parameters while maintaining good accuracy.

### Variable Definitions

Variables and parameters specific to the water heater formulation are summarized in the following table.

| Variable/Parameter | Description | Units |
|---|---|---|
| $ S^{WH}_{k} $ | Power allocated to the water heater at time $ k $ | W |
| $ X^{WH}_{k} $ | Water temperature at time $ k $ | °C |
| $ X^{d}_{WH} $ | Desired water temperature (constant) | °C |
| $ P_{WH} $ | Priority weight for the water heater | - |
| $ \Delta \alpha_{WH} $ | Normalization factor (e.g., 50 K) | K |
| $ C $ | Water heater thermal constant (thermal capacity per volume) | Wh/°C/L |
| $ V $ | Tank volume | m³ |
| $ \dot{V}_{k} $ | Water flow rate at time $ k $ | m³/s |
| $ X_{\text{inlet}} $ | Inlet water temperature | °C |
| $ T_a $ | Ambient temperature | °C |
| $ \underline{X}^{WH} $ | Minimum water temperature | °C |
| $ \overline{X}^{WH} $ | Maximum water temperature | °C |
| $ S^{WH,\max} $ | Maximum water heater power | W |
| $ X^{WH}_{\text{initial}} $ | Initial water temperature | °C |
| $ \Delta t $ | Time step duration | h |



## Classes

This module defines the `WaterHeaterMPC` class, which models an electric water heater for MPC.

It extends the abstract `DeviceMPC` class, providing a concrete implementation for formulating the optimization problem specific to controlling a water heater. This includes defining objectives related to maintaining water temperature within a desired range and incorporating constraints such as power limits, tank volume, and thermal dynamics influenced by ambient temperature and water flow.

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

