---
sidebar_position: 3
---

# Electric Storage

The electric storage system, typically a household battery, plays a key role in residential energy management by offering the flexibility to store and release energy during peak events. By optimizing battery charging and discharging, the Model Predictive Control (MPC) strategy enables efficient energy allocation while respecting user state-of-charge objectives and grid constraints. This section presents the MPC formulation for the electric storage device, which balances energy cost, user comfort, and battery operational limits. The formulation is based on predictive modeling to anticipate battery behavior over a time horizon, allowing proactive power peak management during service restoration.

The electric storage formulation is designed to minimize deviations from a desired SoC, while considering dynamic electricity rates, battery efficiency, and self-discharge characteristics. The use of a convex optimization framework ensures the feasibility of calculations, allowing the MPC to run efficiently on embedded devices with limited resources. This approach was chosen to provide a robust and scalable solution capable of adapting to varying grid conditions and user preferences, making it suitable for integration into HEMS.

### Optimization Formulation
The MPC formulation for the electric storage device optimizes charging and discharging power over a prediction horizon $ T $, with time steps of duration $ \Delta t $ (derived from the optimization interval, e.g., 10 minutes). The objective is to minimize the comfort penalty, defined as the quadratic deviation between the battery's residual energy and a desired SoC, weighted by a user-defined priority. The power allocation cost is integrated into the overall MPC objective, but for electric storage, only the comfort term is device-specific here.

The comfort penalty for electric storage is formulated as follows:
$$
J_{BS,k} = P_{BS} \sum_{k=1}^{T} \left( \frac{X^{d}_{BS} - X^{BS}_{k}}{\Delta \alpha_{BS}} \right)^2
$$

where:
- $ P_{BS} $ is the priority weight for electric storage.
- $ X^{d}_{BS} $ is the desired state of charge (constant over the horizon).
- $ X^{BS}_{k} $ is the residual energy (SoC) at time $ k $.
- $ \Delta \alpha_{BS} $ is the normalization factor, generally defined as the battery's energy capacity.

The dynamics of electric storage are governed by the evolution of the battery's state of charge, which accounts for charging and discharging efficiencies as well as self-discharge:
$$
X^{BS}_{k+1} = \gamma X^{BS}_{k} + \left( \eta_c S^{BS-C}_{k} - \frac{S^{BS-D}_{k}}{\eta_d} \right) \Delta t, \quad \forall k
$$
where:
- $ \gamma $ is the degradation factor representing self-discharge.
- $ \eta_c $ is the charging efficiency.
- $ \eta_d $ is the discharging efficiency.
- $ S^{BS-C}_{k} $ is the charging power at time $ k $.
- $ S^{BS-D}_{k} $ is the discharging power at time $ k $.
- $ \Delta t $ is the duration of the time step (in hours).

The constraints ensure that the battery operates within its physical and operational limits:
- **Residual Energy Limits**:
$$
\underline{X}^{BS} \leq X^{BS}_{k} \leq \overline{X}^{BS}, \quad \forall k
$$
where $ \underline{X}^{BS} $ and $ \overline{X}^{BS} $ are the minimum and maximum residual energy, respectively.
- **Power Limits**:
$$
0 \leq S^{BS-C}_{k} \leq S^{BS,\max}, \quad 0 \leq S^{BS-D}_{k} \leq S^{BS,\max}, \quad \forall k
$$
where $ S^{BS,\max} $ is the maximum battery power.
- **Initial Condition**:
$$
X^{BS}_{0} = X^{BS}_{\text{initial}}
$$
where $ X^{BS}_{\text{initial}} $ is the initial state of charge.
- **Final SoC Requirement**:
$$
X^{BS}_{T} \geq X^{BS}_{\text{final}}
$$
where $ X^{BS}_{\text{final}} $ is the required state of charge at the end of the horizon.

The net power provided by electric storage, which contributes to the overall power constraint, is:
$$
S^{BS}_{k} = S^{BS-C}_{k} - S^{BS-D}_{k}, \quad \forall k
$$

### Justification of the Formulation
The formulation prioritizes user comfort by minimizing the deviation from a desired SoC, which is essential to ensure the battery can power critical loads during peak events. The inclusion of charging and discharging efficiencies ($ \eta_c $, $ \eta_d $) as well as the degradation factor ($ \gamma $) allows for accurate modeling of real battery behavior, which improves the accuracy of MPC predictions. The convex formulation avoids the use of binary variables for charge/discharge exclusivity to reduce computational complexity, which is crucial for real-time applications in embedded devices. The assumption of a constant desired SoC simplifies optimization, while corresponding to typical residential use cases where users generally prefer a stable target SoC.

### Variable Definitions
The variables and parameters specific to the electric storage formulation are summarized in the following table:

| Variable/Parameter | Description | Units |
|---|---|---|
| $ S^{BS-C}_{k} $ | Charging power at time $ k $ | W |
| $ S^{BS-D}_{k} $ | Discharging power at time $ k $ | W |
| $ S^{BS}_{k} $ | Net power at time $ k $ | W |
| $ X^{BS}_{k} $ | Residual energy (SoC) at time $ k $ | Wh |
| $ X^{d}_{BS} $ | Desired state of charge (constant) | Wh |
| $ P_{BS} $ | Priority weight for electric storage | - |
| $ \Delta \alpha_{BS} $ | Normalization factor (generally energy capacity) | Wh |
| $ \gamma $ | Degradation factor (self-discharge) | - |
| $ \eta_c $ | Charging efficiency | - |
| $ \eta_d $ | Discharging efficiency | - |
| $ S^{BS,\max} $ | Maximum power capacity | W |
| $ \underline{X}^{BS} $ | Minimum residual energy | Wh |
| $ \overline{X}^{BS} $ | Maximum residual energy | Wh |
| $ X^{BS}_{\text{initial}} $ | Initial state of charge | Wh |
| $ X^{BS}_{\text{final}} $ | Required final state of charge | Wh |
| $ \Delta t $ | Time step duration | h |



## Classes

### `ElectricStorageMPC`
This module defines the `ElectricStorageMPC` class, which models an electric battery storage system for MPC.

It extends the abstract `DeviceMPC` class, providing a concrete implementation for formulating the optimization problem specific to battery charging and discharging. This includes defining objectives related to maintaining a desired state of charge and incorporating constraints such as power limits and energy balance equations.

This class models the behavior of a stationary battery energy storage system (BESS). It formulates the optimization problem for charging and discharging the battery to meet certain objectives (e.g., maintaining a desired state of charge) while respecting the physical limitations of the device.

#### Methods

##### `__init__(devices: List[Dict[str, Any]])`

Initializes the `ElectricStorageMPC`.

**Args:**

- `devices`: A list of dictionaries, where each dictionary contains the configuration and parameters of an electric storage device.

##### `create_mpc_formulation(start: datetime, stop: datetime, steps_horizon_k: int, interval: int = 10, norm_factor: int = 10)`

Creates the optimization formulation for the electric storage device.

This method builds a CVXPY optimization problem that models the battery's behavior over the prediction horizon. The objective is to minimize the deviation from a desired state of charge, while adhering to constraints such as:
- State of charge (SoC) limits (min and max).
- Charging and discharging power limits.
- The energy balance equation that governs how SoC changes over time.

**Args:**

- `start`: The start time of the optimization horizon.
- `stop`: The end time of the optimization horizon.
- `steps_horizon_k`: The number of time steps in the horizon.
- `interval`: The duration of each time step in minutes.
- `norm_factor`: A normalization factor for the objective function.

**Returns:**

- A tuple containing the objective terms, constraints, and the dispatch variable for the CVXPY optimization problem.
