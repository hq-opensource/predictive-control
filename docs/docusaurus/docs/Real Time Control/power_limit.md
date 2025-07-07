---
sidebar_position: 1
---

# Real-Time Control

While Model Predictive Control (MPC) proactively optimizes power allocation for controllable devices based on predictive models and forecasts of uncontrollable loads, it cannot anticipate random and unforeseen consumption events, such as a user turning on an oven or other high-consumption appliances. These unforeseen loads can lead to grid capacity exceedance, risking the triggering of protection mechanisms and subsequent outages. Real-Time Control (RTC) acts as a real-time monitor, continuously observing energy consumption and dynamically adjusting controllable loads to enforce the power limit in case of unexpected overloads. This section presents the RTC formulation, which relies on real-time measurements and an inverse priority mechanism to maintain grid stability and enhance the reliability of residential energy management systems.

RTC checks total energy consumption against a threshold defined by the provider's power limit minus a safety margin. When this threshold is exceeded, RTC reduces controllable loads in decreasing order of priority (i.e., least important devices first) to minimize impact on user comfort. The formulation includes an anti-rebound mechanism to prevent rapid and repeated adjustments, as well as a notification system to alert users when reduction is insufficient. Lightweight and reactive, RTC operates as a continuous control loop, making it suitable for implementation on embedded devices alongside MPC. This dual-control approach allows for both predictive optimization and immediate correction, providing a robust solution for Demand Response (DR) mitigation.

### Necessity of Real-Time Control

MPC excels at anticipating recurrent behaviors and optimizing power allocation based on forecasts, such as those generated for uncontrollable loads by the Python Prophet library. By controlling devices like electric storage systems, water heaters, space heating, and electric vehicles (EVs), MPC minimizes energy costs while maintaining user comfort under normal conditions. However, its predictive nature depends on the accuracy of forecasts, which cannot account for sporadic, user-initiated consumption (e.g., activating an oven or other energy-intensive appliances). These random events cause sudden demand peaks that MPC cannot manage proactively, risking violation of the provider-imposed power limit and grid destabilization. RTC addresses this limitation by acting as a second-level control, monitoring consumption in real-time and instantly reducing controllable loads when necessary. This real-time intervention ensures compliance with the grid power limit, preventing cascading failures during service restoration, while complementing MPC's strategic planning with immediate corrective action.

### Optimization Formulation

RTC aims to enforce the provider-imposed power limit by minimizing the reduction of controllable loads while ensuring:
$$
S^{\text{total}}_k \leq S^L_k, \quad \forall k
$$
where:
- $ S^{\text{total}}_k = \sum_{w \in W} S^{\text{RTC}}_{w,k} + S^U_k $ is the total consumption at time $ k $ (in kW), including the adjusted power of controllable devices $ S^{\text{RTC}}_{w,k} $ and the uncontrollable load $ S^U_k $.
- $ S^L_k $ is the power limit imposed by the provider at time $ k $ (in kW).

RTC activates when total consumption exceeds a threshold defined by the power limit minus a safety margin:
$$
S^{\text{total}}_k > S^L_k - M_k, \quad \forall k
$$
where $ M_k $ is the safety margin at time $ k $, typically set to 0.5 kW.

When reduction is necessary, RTC adjusts the power of controllable devices $ w \in W $ according to an inverse priority order, first reducing devices with the lowest priority weights $ P_w $ (defined in MPC). The adjusted power for each device is:
$$
S^{\text{RTC}}_{w,k} = \text{critical\_action}_w, \quad \text{if } w = w_{\text{next}}
$$
where:
- $ \text{critical\_action}_w $ is the device-specific critical action (e.g., minimum setpoint), defined in advance for each device for the user.
- $ w_{\text{next}} $ is the next device to reduce, selected according to:
$$
w_{\text{next}} = \arg\min_{w \in W_{\text{avail}}} P_w
$$
where $ W_{\text{avail}} $ is the set of controllable devices that can be adjusted, respecting an anti-rebound time constraint.

The anti-rebound time constraint prevents frequent adjustments on the same device:
$$
t - t^{\text{last}}_w > \tau_w, \quad \forall w
$$
where:
- $ t $ is the current time.
- $ t^{\text{last}}_w $ is the time of the last adjustment for device $ w $.
- $ \tau_w $ is the anti-rebound time for device $ w $, typically 5 seconds for most devices and 30 seconds for batteries, due to their sensitivity to frequent variations.

If no further reduction is possible (i.e., all devices have been adjusted to their critical action) and the power limit is still exceeded, a user notification is triggered:
$$
\text{Notify}_k =
\begin{cases}
1 & \text{if } S^{\text{total}}_k > S^L_k \\
0 & \text{otherwise}
\end{cases}
$$
where $ \text{Notify}_k = 1 $ means a notification (e.g., "Reduce uncontrollable load usage") is sent to the user, prompting manual intervention.

### Inverse Priority Mechanism

RTC uses an inverse priority mechanism to determine the reduction order, relying on the same priority weights $ P_w $ as defined in MPC. Devices with low $ P_w $ values, thus considered less important to the user, are reduced first to limit the impact on more critical devices. For example, a water heater with low priority might be turned off before a heater in an occupied room. This approach is consistent with MPC's user-centric optimization, while ensuring a rapid response in case of power limit exceedance. Priorities are sorted at initialization, and RTC iterates through devices in this order, applying reductions only to devices that respect the anti-rebound constraint.

### Justification of the Formulation

The RTC formulation aims to provide a lightweight and reactive solution for managing unforeseen consumption in real-time. Threshold-based activation with a safety margin $ M_k $ avoids unnecessary interventions, preserving MPC's optimized schedule under normal conditions. The inverse priority mechanism ensures that reductions respect user preferences, maintaining comfort for high-priority devices. The anti-rebound time constraint protects equipment by limiting frequent adjustments, especially for sensitive devices like batteries. The notification system engages users when automatic reductions are insufficient, fostering cooperation in demand management. Operating as a continuous control loop with a short monitoring interval (e.g., 1 second), RTC ensures a rapid response to demand peaks, complementing MPC's predictive capabilities with immediate corrective action.

### Variable Definitions

Variables and parameters specific to the RTC formulation are summarized in the following table. Device-specific priorities $ P_w $ are defined in the corresponding MPC subsections.

| Variable/Parameter | Description | Units |
|---|---|---|
| $ S^{\text{total}}_k $ | Total consumption at time $ k $ | kW |
| $ S^{\text{RTC}}_{w,k} $ | Adjusted power of device $ w $ after RTC action at time $ k $ | kW |
| $ S^U_k $ | Consumption of uncontrollable loads at time $ k $ | kW |
| $ S^L_k $ | Power limit imposed by the provider at time $ k $ | kW |
| $ M_k $ | Safety margin at time $ k $ | kW |
| $ \text{Notify}_k $ | Binary variable indicating a user notification at time $ k $ | - |
| $ P_w $ | Priority weight of device $ w $ (from MPC) | - |
| $ W_{\text{avail}} $ | Set of controllable devices available for reduction | - |
| $ \text{critical\_action}_w $ | Device-specific critical action (e.g., shutdown or minimum setpoint) | Variable |
| $ t $ | Current time | s |
| $ t^{\text{last}}_w $ | Time of last adjustment for device $ w $ | s |
| $ \tau_w $ | Anti-rebound time for device $ w $ | s |


## Classes

This module implements the Real-Time Control (RTC) mechanism for enforcing power limits.

It defines the `RealTimeControl` class, which operates as a separate thread to continuously monitor the total building power consumption. When consumption exceeds a predefined dynamic power limit, the RTC applies curtailment actions to controllable devices based on their priorities and a debounce mechanism to prevent rapid cycling. This module is critical for ensuring that the building's power consumption adheres to grid constraints in real-time.

### `RealTimeControl`

Implements a Real-Time Control (RTC) mechanism to enforce power limits.

This class operates as a separate thread, continuously monitoring the total building power consumption and comparing it against a dynamic power limit. If the consumption exceeds the limit, it applies curtailment actions to controllable devices based on their priorities and a debounce mechanism. It also includes logging and a placeholder for user notifications.

#### Methods

##### `__init__(power_limit: Dict[datetime, float], space_heating: bool, electric_storage: bool, electric_vehicle: bool, water_heater: bool)`

Initializes the `RealTimeControl` thread.

**Args:**

- `power_limit`: A dictionary mapping timestamps to the maximum allowable power consumption at those times.
- `space_heating`: A boolean indicating whether space heating devices are controllable.
- `electric_storage`: A boolean indicating whether electric storage devices are controllable.
- `electric_vehicle`: A boolean indicating whether electric vehicle devices are controllable.
- `water_heater`: A boolean indicating whether water heater devices are controllable.

##### `run()`

Main control loop for real-time power limit enforcement.

This method continuously monitors the total power consumption and, if necessary, applies curtailment actions to controllable devices. It prioritizes devices based on their configured priorities and respects a debounce time to prevent rapid cycling of controls. The loop runs as long as `self.must_run` is True.
