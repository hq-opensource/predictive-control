"""
The `real_time` module is dedicated to implementing the Real-Time Control (RTC) mechanism
for enforcing dynamic power limits within the building. This module is crucial for
maintaining grid stability and ensuring the building's power consumption adheres to
predefined constraints in real-time.

Key functionalities and components include:

- [`power_limit_mpc.py`](src/cold_pickup_mpc/real_time/power_limit_mpc.py): This submodule defines the `RealTimeControl` class,
  which operates as a separate thread to continuously monitor the total building
  power consumption. It implements the core logic for applying curtailment actions
  to controllable devices when consumption exceeds the dynamic power limit. It
  incorporates device prioritization, a debounce mechanism to prevent rapid cycling,
  and logging for operational transparency. This module is essential for the
  real-time enforcement of power constraints.
"""
