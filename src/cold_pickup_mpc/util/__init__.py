"""
The `util` module provides a collection of general-purpose utility functions and
classes that support various aspects of the Model Predictive Control (MPC) application.
These utilities are designed to promote code reusability, maintain consistency,
and simplify common tasks across different modules.

Key functionalities and components include:

- [`logging.py`](src/cold_pickup_mpc/util/logging.py): This submodule offers a centralized utility for configuring and
  managing application logging. It defines the `LoggingUtil` class, which provides
  a static method to retrieve pre-configured logger instances, ensuring consistent
  logging practices, standardized log formats, and dynamic adjustment of log levels
  via environment variables.
"""
