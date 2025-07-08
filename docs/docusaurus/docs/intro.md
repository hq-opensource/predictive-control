---
sidebar_position: 1
---

# Predictive Control

The `predictive_control` package provides a hybrid control strategy combining Model Predictive Control (MPC) and Real-Time Control (RTC) to intelligently manage energy in highly electrified residential homes.

## System Architecture

This package is a key component within a larger **Building Intelligence** ecosystem, as illustrated in the architecture diagram below. It is designed to run as a service that consumes data from the central `Core API` of the Building Intelligence platform.

![Building Intelligence Diagram](/img/hems_predictive.png)

The diagram shows three primary layers:
1.  **Smart Devices:** The source of data from various building assets (e.g., HVAC, EV chargers) using protocols like Modbus and Bacnet.
2.  **Building Intelligence Platform:** The core infrastructure (a separate software repository) that gathers, stores, and processes data, making it available via a `Core API`.
3.  **Grid Services:** A set of applications that consume the API data to provide value-added services.

The `predictive_control` package provides the implementation for the grid services highlighted in red: **CLPU - Predictive (MPC+RTC)** and **Dynamic Tariffs (MPC)**. If you want more information about the main platform, you can visit its [**Documentation**](https://hq-opensource.github.io/building-intelligence/) or [**GitHub Repository**](https://github.com/hq-opensource/building-intelligence).


# Objectives and Applications

The `predictive_control` package provides a robust and flexible control system designed to intelligently manage energy consumption in highly electrified residential homes. While initially developed to address the challenges of **Cold Load Pickup (CLPU)**—the large, synchronized power demand that occurs after a power outage—its hybrid control strategy of Model Predictive Control (MPC) and Real-Time Control (RTC) extends its applicability to a wide range of energy management scenarios.

Instead of relying solely on grid-side solutions, this package implements a user-centric approach, intelligently coordinating controllable devices (e.g., HVAC, water heaters, electric vehicles, batteries) to optimize energy usage while respecting grid limits and user preferences. The entire system is designed to be computationally efficient for deployment on low-power edge devices, such as a Home Energy Management System (HEMS).

The hybrid strategy is twofold:
1.  **Predictive Planning (MPC):** The MPC component proactively schedules device operation over a future horizon. It creates an optimal plan that minimizes energy costs and respects user comfort (e.g., temperature setpoints, battery state of charge targets), considering forecasts for weather and non-controllable loads.
2.  **Real-Time Control (RTC):** The RTC component acts as a high-frequency safeguard. It continuously monitors the building's total power consumption and, if it exceeds a predefined limit, curtails low-priority devices. This handles unforeseen consumption spikes not captured by the MPC's plan, ensuring strict adherence to power constraints.

## Broader Applications

The inherent sensitivity of the optimization formulations to energy prices (dynamic tariffs, hourly tariffs, retail energy market signals) and the flexible control mechanisms enable the `predictive_control` package to be applied in various scenarios beyond CLPU:

*   **General Demand Response (DR) Programs:** Facilitating participation in peak shaving, load shifting, and potentially ancillary services by optimizing consumption during high-demand or high-price periods.
*   **Energy Cost Optimization for Consumers:** Maximizing savings under Time-of-Use (ToU) tariffs, Real-Time Pricing (RTP), or other dynamic pricing schemes by shifting loads to cheaper periods.
*   **Integration with Distributed Energy Resources (DERs):** Optimizing the use of local generation (e.g., solar PV) through self-consumption strategies and intelligent battery energy management (charging/discharging based on prices and availability).
*   **Grid Resilience and Stability:** Contributing to grid stability by managing congestion, providing voltage support, and enabling structured emergency load shedding.
*   **Building Energy Efficiency and Sustainability:** Reducing the building's carbon footprint by aligning energy consumption with periods of higher renewable energy availability and promoting overall energy efficiency.

## Sub-packages

- **devices**: Contains modules that define and model the behavior of all controllable devices. It provides a standardized `DeviceMPC` interface and specific implementations for assets like electric storage, electric vehicles, space heaters, and water heaters.

- **mpc**: The core of the predictive planning, responsible for the main MPC logic. It builds the global optimization problem from individual device models, executes the solver, interprets the results, and posts the final control schedules.

- **real_time**: Implements the high-frequency Real-Time Control (RTC) loop. It runs independently to enforce dynamic power limits, providing a rapid, reactive response to prevent constraint violations from unforeseen events.

- **retrievers**: Manages all data acquisition for the MPC. It contains functions and classes to fetch static and time-series data from a Core API, including device states, weather forecasts, and user preferences.

- **thermal_model**: Provides the tools to model the thermal dynamics of building zones and appliances. It includes modules for both defining the thermal models and for learning their parameters from historical data.

- **util**: A collection of general-purpose utilities that support the application, most notably a centralized logging utility for consistent, configurable logging across all modules.

Together, these components provide a powerful framework for advanced, predictive control of building energy resources, specifically tailored for the CLPU challenge.
