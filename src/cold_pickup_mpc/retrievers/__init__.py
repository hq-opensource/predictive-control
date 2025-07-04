"""
The `retrievers` module is responsible for abstracting and implementing the data
retrieval mechanisms required by the Model Predictive Control (MPC) system. It
provides a structured way to fetch both static properties and dynamic (time-series)
data from various sources, primarily the Core API. This module ensures that the MPC
models have access to all necessary inputs for accurate optimization and control.

Key functionalities and components include:

- [`api_calls.py`](src/cold_pickup_mpc/retrievers/api_calls.py): This submodule provides a collection of API client functions
  for retrieving diverse data types, including device information, device states,
  building consumption, user preferences, historical data, and weather forecasts
  from the Core API. It acts as the primary interface for external data access.

- [`device_retriever.py`](src/cold_pickup_mpc/retrievers/device_retriever.py): This submodule defines the abstract base class
  `DeviceRetriever`, which establishes a common interface for all device-specific
  data retrievers. Subclasses extend this to implement logic for fetching data
  relevant to their particular device types.

- [`electric_storage_retriever.py`](src/cold_pickup_mpc/retrievers/electric_storage_retriever.py): This submodule implements the
  `ElectricStorageDataRetriever` class, a concrete `DeviceRetriever` for electric
  battery storage systems. It handles the retrieval of static parameters and dynamic
  data such as initial State of Charge (SoC) and SoC preference profiles.

- [`electric_vehicle_v1g_retriever.py`](src/cold_pickup_mpc/retrievers/electric_vehicle_v1g_retriever.py): This submodule defines
  the `ElectricVehicleV1gDataRetriever` class, specializing in data retrieval for
  unidirectional (V1G) electric vehicle charging. It fetches initial SoC, SoC
  preference profiles, and branched (connection) profiles.

- [`space_heating_retriever.py`](src/cold_pickup_mpc/retrievers/space_heating_retriever.py): This submodule provides the
  `SpaceHeatingDataRetriever` class, which is responsible for fetching data related
  to space heating systems (e.g., smart thermostats). It retrieves initial indoor
  temperatures, setpoint preferences, occupancy preferences, and weather forecasts,
  and integrates with the thermal model learning component.

- [`water_heater_retriever.py`](src/cold_pickup_mpc/retrievers/water_heater_retriever.py): This submodule implements the
  `WaterHeaterDataRetriever` class for electric water heaters. It handles the
  retrieval of initial water temperature, hot water consumption preferences, and
  ambient temperature data.
"""
