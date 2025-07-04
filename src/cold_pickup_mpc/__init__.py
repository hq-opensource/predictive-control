"""
The `cold_pickup_mpc` package provides a hybrid control strategy combining
Model Predictive Control (MPC) and Real-Time Control (RTC) to mitigate the
Cold Load Pickup (CLPU) phenomenon in highly electrified buildings.

Its primary purpose is to manage the large, synchronized power demand that
occurs after a power outage. Instead of relying on grid-side solutions, this
package implements a user-centric approach, intelligently coordinating controllable
devices (e.g., HVAC, water heaters, electric vehicles, batteries) to smooth the
reconnection process while respecting grid limits and user preferences. The
entire system is designed to be computationally efficient for deployment on
low-power edge devices, such as a Home Energy Management System (HEMS).

The hybrid strategy is twofold:
1.  **Predictive Planning (MPC):** The MPC component proactively schedules device
    operation over a future horizon. It creates an optimal plan that minimizes
    energy costs and respects user comfort (e.g., temperature setpoints, battery
    state of charge targets), considering forecasts for weather and non-controllable
    loads.
2.  **Reactive Supervision (RTC):** The RTC component acts as a high-frequency
    safeguard. It continuously monitors the building's total power consumption
    and, if it exceeds a predefined limit, curtails low-priority devices. This
    handles unforeseen consumption spikes not captured by the MPC's plan,
    ensuring strict adherence to power constraints.

Sub-packages:
-------------
- `devices`:
  Contains modules that define and model the behavior of all controllable
  devices. It provides a standardized `DeviceMPC` interface and specific
  implementations for assets like electric storage, electric vehicles, space
  heaters, and water heaters.

- `mpc`:
  The core of the predictive planning, responsible for the main MPC logic. It
  builds the global optimization problem from individual device models, executes
  the solver, interprets the results, and posts the final control schedules.

- `real_time`:
  Implements the high-frequency Real-Time Control (RTC) loop. It runs
  independently to enforce dynamic power limits, providing a rapid, reactive
  response to prevent constraint violations from unforeseen events.

- `retrievers`:
  Manages all data acquisition for the MPC. It contains functions and classes
  to fetch static and time-series data from a Core API, including device
  states, weather forecasts, and user preferences.

- `thermal_model`:
  Provides the tools to model the thermal dynamics of building zones and
  appliances. It includes modules for both defining the thermal models and for
  learning their parameters from historical data.

- `util`:
  A collection of general-purpose utilities that support the application,
  most notably a centralized logging utility for consistent, configurable
  logging across all modules.

Together, these components provide a powerful framework for advanced, predictive
control of building energy resources, specifically tailored for the CLPU challenge.
"""
