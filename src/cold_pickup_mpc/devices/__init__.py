"""This package defines and manages the various controllable devices integrated into the Model Predictive Control (MPC) system.

It provides the foundational structures and implementations for modeling different
device types, interacting with them via API calls, and formulating their
contributions to the overall MPC optimization problem.

The key modules within this package include:
- `api_calls.py`: Contains functions for direct communication with the Core API
  to retrieve device information, current states, and send control commands.
- `device_mpc.py`: Defines the abstract base class `DeviceMPC`, which establishes
  a standardized interface for all controllable devices to expose their
  optimization formulations (objectives, constraints, and dispatch variables).
- `electric_storage_mpc.py`: Implements the `DeviceMPC` interface for electric
  battery storage systems, modeling their charging and discharging behavior.
- `electric_vehicle_v1g_mpc.py`: Implements the `DeviceMPC` interface for
  unidirectional (V1G) electric vehicles, focusing on their charging optimization.
- `helper.py`: Provides utility functions and an enumeration (`DeviceHelper`)
  for categorizing, filtering, and sorting devices based on their properties and priorities.
- `space_heating_mpc.py`: Implements the `DeviceMPC` interface for space heating
  systems, modeling thermal zones and heater control.
- `water_heater_mpc.py`: Implements the `DeviceMPC` interface for electric water
  heaters, modeling their thermal dynamics and power consumption.

Together, these modules enable the MPC system to understand, control, and optimize
the operation of a diverse set of building devices.
"""
