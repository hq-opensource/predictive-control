---
sidebar_position: 4
---

# Electric Vehicle V1G MPC

The electric vehicle (EV) is an important component of modern residential energy systems, contributing to power demand during charging, especially in highly electrified homes subject to Demand Response (DR) events. The Model Predictive Control (MPC) formulation for the EV optimizes charging to maintain a desired State of Charge (SoC) while respecting grid power constraints and user preferences, such as EV availability for charging. This section presents the EV MPC formulation in V1G mode (charging only), which uses a continuous control variable to modulate charging power based on a branched profile indicating when the EV is connected. This approach enables efficient and flexible power allocation during service restoration, enhancing grid stability and integration with Home Energy Management Systems (HEMS).

The EV formulation uses a continuous control variable (0-1) to model the charging power modulation, combined with a branched profile reflecting EV availability (e.g., when plugged in). This design balances user comfort by minimizing SoC deviations and ensures computational efficiency through a linear programming framework, while providing precise power control. The integration of charging efficiency and self-discharge improves model accuracy, while the branched profile allows the controller to adapt to user schedules, making it practical for residential applications.

### Optimization Formulation

The MPC formulation for the EV optimizes charging power over a prediction horizon $T$, with time steps of duration $\Delta t$ (e.g., 10 minutes). The objective is to minimize the comfort penalty, defined as the squared deviation between the measured residual energy and a desired residual energy, weighted by a user-defined priority. The power allocation cost is included in the overall MPC objective, while the comfort term is specific to the EV.

The comfort penalty is formulated as follows:
$$
J_{EV,k} = P_{EV} \sum_{k=1}^{T} \left( \frac{X^{d}_{EV} - X^{EV}_{k}}{\Delta \alpha_{EV}} \right)^2
$$
where:
- $ P_{EV} $ is the priority weight for the EV.
- $ X^{d}_{EV} $ is the desired state of charge (constant, e.g., 90% of energy capacity).
- $ X^{EV}_{k} $ is the residual energy at time $ k $.
- $ \Delta \alpha_{EV} $ is the normalization factor (typically the EV's energy capacity).

The dynamics of the EV's state of charge are modeled as follows:
$$
X^{EV}_{k+1} = \gamma X^{EV}_{k} + \eta_c S^{EV-C}_{k} \Delta t, \quad \forall k
$$
where:
- $ \gamma $ is the degradation factor representing self-discharge.
- $ \eta_c $ is the charging efficiency.
- $ S^{EV-C}_{k} $ is the charging power at time $ k $.
- $ \Delta t $ is the duration of the time step (in hours).

Charging power is controlled by a continuous variable and EV availability:
$$
S^{EV-C}_{k} = U^{EV}_{k} B_{k} S^{EV,\max}, \quad \forall k
$$
where:
- $ U^{EV}_{k} \in [0, 1] $ is the continuous variable controlling the charging power level at time $ k $.
- $ B_{k} \in \{0, 1\} $ is the branched profile indicating EV availability (1 if connected, 0 otherwise).
- $ S^{EV,\max} $ is the maximum charging power.

Constraints ensure that the EV operates within its physical and operational limits:
- **Residual Energy Limits**:
$$
\underline{X}^{EV} \leq X^{EV}_{k} \leq \overline{X}^{EV}, \quad \forall k
$$
where $ \underline{X}^{EV} $ and $ \overline{X}^{EV} $ are the minimum and maximum residual energies (e.g., 25% and 95% of energy capacity).
- **Power Limits**:
$$
0 \leq S^{EV-C}_{k} \leq S^{EV,\max}, \quad \forall k
$$
where $ S^{EV,\max} $ is the maximum charging power.
- **Initial Condition**:
$$
X^{EV}_{0} = X^{EV}_{\text{initial}}
$$
where $ X^{EV}_{\text{initial}} $ is the initial state of charge.
- **Final SoC Requirement**:
$$
X^{EV}_{T} \geq X^{EV}_{\text{final}}
$$
where $ X^{EV}_{\text{final}} $ is the required state of charge at the end of the horizon.
- **Power Ramping Constraints** (optional, for smoother transitions):
$$
|U^{EV}_{k+1} - U^{EV}_{k}| \leq R^{EV}_{\max}, \quad \forall k \in [1, T-1]
$$
where $ R^{EV}_{\max} $ is the maximum allowed rate of change in the control variable between consecutive time steps. This constraint can be enabled or disabled via the `enable_ramping` parameter and helps ensure smoother power transitions, reducing stress on the battery and improving grid stability. The ramping rate typically ranges from 0.1 to 0.5 per time step.

The power allocated to the EV, which contributes to the global power constraint, is:
$$
S^{EV}_{k} = S^{EV-C}_{k}, \quad \forall k
$$

### Ramping Constraints for Smooth Power Transitions

The EV MPC implementation includes optional power ramping constraints that limit the rate of change in charging power between consecutive time steps. These constraints provide several benefits:

**Benefits of Ramping Constraints:**
- **Battery Health**: Gradual power changes reduce stress on the battery system
- **Grid Stability**: Smooth transitions minimize sudden load changes that could affect grid stability
- **User Comfort**: Reduced electrical noise and smoother operation
- **Hardware Protection**: Prevents rapid switching that could stress charging infrastructure

**Mathematical Implementation:**
The ramping constraints are implemented by limiting the change in the continuous control variable $ U^{EV}_{k} $ between consecutive time steps:
$$
U^{EV}_{k+1} - U^{EV}_{k} \leq R^{EV}_{\max}
$$
$$
U^{EV}_{k} - U^{EV}_{k+1} \leq R^{EV}_{\max}
$$

**Configuration Parameters:**
- `enable_ramping`: Boolean flag to enable/disable ramping constraints (default: `True`)
- `max_power_ramp_rate`: Maximum allowed rate of change per time step (default: `0.2`)

**Validation Results:**
Extensive testing has demonstrated that ramping constraints:
- Shape the entire optimization trajectory, not just individual transitions
- Work seamlessly with continuous control to provide precise power management
- Allow fractional switch values that represent optimal power modulation
- Maintain optimization effectiveness while ensuring smoother operation

The ramping constraints are particularly valuable in scenarios with frequent charging schedule changes or when grid stability is a priority. They can be easily disabled for applications where maximum charging flexibility is preferred over smooth transitions.

### Justification of the Formulation

The EV formulation uses a continuous control variable (0-1) to model the charging power modulation, which provides flexible power allocation while maintaining computational efficiency through a linear programming framework. This continuous approach allows for precise power control and better integration with grid-level optimization, especially during demand response events where partial charging may be more beneficial than simple on/off control. The branched profile $ B_{k} $ accounts for user schedules, ensuring that charging only occurs when the EV is connected—a critical aspect for residential applications where the vehicle may be unplugged during the day. The comfort penalty favors maintaining a desired residual energy state, ensuring the vehicle is ready for use while reducing demand peaks during DR events. The integration of charging efficiency and self-discharge improves model accuracy, while the linear formulation ensures computational efficiency and fast convergence. This approach is well-suited for real-time optimization on embedded devices and facilitates integration with HEMS by respecting user priorities and grid constraints while providing smooth power modulation capabilities.

### Variable Definitions

Variables and parameters specific to the EV formulation are summarized in the following table.

| Variable/Parameter | Description | Units |
|---|---|---|
| $ S^{EV-C}_{k} $ | Charging power at time $ k $ | W |
| $ S^{EV}_{k} $ | Power allocated to the EV at time $ k $ | W |
| $ X^{EV}_{k} $ | Residual energy (SoC) at time $ k $ | Wh |
| $ X^{d}_{EV} $ | Desired state of charge (constant) | Wh |
| $ U^{EV}_{k} $ | Continuous variable for charging power level at time $ k $ (0-1) | - |
| $ B_{k} $ | Branched profile (0 or 1) indicating EV availability at time $ k $ | - |
| $ R^{EV}_{\max} $ | Maximum allowed ramping rate for control variable | - |
| $ P_{EV} $ | Priority weight for the EV | - |
| $ \Delta \alpha_{EV} $ | Normalization factor (typically energy capacity) | Wh |
| $ \gamma $ | Degradation factor (self-discharge) | - |
| $ \eta_c $ | Charging efficiency | - |
| $ S^{EV,\max} $ | Maximum charging power | W |
| $ \underline{X}^{EV} $ | Minimum residual energy | Wh |
| $ \overline{X}^{EV} $ | Maximum residual energy | Wh |
| $ X^{EV}_{\text{initial}} $ | Initial state of charge | Wh |
| $ X^{EV}_{\text{final}} $ | Required final state of charge (if specified) | Wh |
| $ \Delta t $ | Time step duration | h |


## Classes
This module defines the `ElectricVehicleV1GMPC` class, which models a V1G electric vehicle for MPC.

It extends the abstract `DeviceMPC` class, providing a concrete implementation for formulating the optimization problem specific to unidirectional electric vehicle charging. This includes defining objectives related to maintaining a desired state of charge and incorporating constraints such as charging power limits, battery capacity, and the vehicle's connection status.

### `ElectricVehicleV1GMPC`

Represents a V1G (unidirectional charging) Electric Vehicle for the MPC.

This class models an electric vehicle that can only draw power from the grid (V1G - Vehicle-to-Grid unidirectional). It formulates an optimization problem to control the EV's charging schedule based on its availability (i.e., when it is plugged in) and charging preferences, while respecting the vehicle's battery constraints.

#### Methods

##### `__init__(device_info: List[Dict[str, Any]])`

Initializes the `ElectricVehicleV1GMPC`.

**Args:**

- `device_info`: A list containing a single dictionary with the configuration and parameters of the electric vehicle.

##### `create_mpc_formulation(start: datetime, stop: datetime, interval: int, v1g_info: Dict[str, pd.DataFrame])`

Creates the optimization formulation for the V1G electric vehicle.

This method builds a CVXPY optimization problem that determines the optimal charging schedule for the EV. The objective is to minimize the deviation from a desired state of charge. The model includes constraints for:
- SoC limits (min and max).
- Charging power limits.
- The EV's connection status (it can only charge when plugged in, as indicated by the `branched_profile`).
- The energy balance equation for the battery.

**Args:**

- `start`: The start time of the optimization horizon.
- `stop`: The end time of the optimization horizon.
- `interval`: The duration of each time step in minutes.
- `v1g_info`: A dictionary containing DataFrames for the 'initial_state' and 'branched_profile' (connection status) of the EV.

**Returns:**

- A tuple containing the objective terms, constraints, and the dispatch variable for the CVXPY optimization problem.

**Raises:**

- `ValueError`: If the input data (e.g., `branched_profile`, `initial_state`) has incorrect dimensions or values.

