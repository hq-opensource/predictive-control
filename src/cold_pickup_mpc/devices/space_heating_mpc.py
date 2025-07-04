from datetime import datetime
from time import time
from typing import Any, Dict, List, Tuple

import cvxpy as cvx
import numpy as np

from cold_pickup_mpc.devices.device_mpc import DeviceMPC
from cold_pickup_mpc.devices.helper import DeviceHelper
from cold_pickup_mpc.retrievers.space_heating_retriever import SpaceHeatingDataRetriever
from cold_pickup_mpc.util.logging import LoggingUtil

logger = LoggingUtil.get_logger(__name__)


class SpaceHeatingMPC(DeviceMPC):
    """Represents a space heating system (e.g., smart thermostats) for the MPC.

    This class models the thermal behavior of one or more building zones controlled
    by electric heaters. It uses a state-space thermal model to predict temperature
    evolution and formulates an optimization problem to control the heaters' power
    output. The goal is to maintain the indoor temperature close to the desired
    setpoints while respecting comfort boundaries and system constraints.
    """

    def __init__(self, devices: List[Dict[str, Any]]) -> None:
        """Initializes the SpaceHeatingMPC.

        Args:
            devices: A list of dictionaries, where each dictionary contains the
                     configuration and parameters of a space heating device (thermal zone).
        """
        self._space_heating_retriever = SpaceHeatingDataRetriever(devices)

    def create_mpc_formulation(
        self,
        start: datetime,
        stop: datetime,
        steps_horizon_k: int,
        interval: int = 10,
        norm_factor: int = 10,  # Default 10°C (max_setpoint - min_setpoint)
    ) -> Tuple[List, List, cvx.Variable]:
        """Creates the optimization formulation for the space heating system.

        This method constructs a CVXPY optimization problem based on a linear
        state-space model of the building's thermal dynamics. The objective function
        penalizes deviations from temperature setpoints, weighted by occupancy and
        user-defined priorities. The constraints include:
        - The state-space thermal balance equation.
        - Temperature comfort bounds (min and max setpoints).
        - Maximum power output of the heaters.
        - Ramping limits on heater power to prevent rapid cycling.

        Args:
            start: The start time of the optimization horizon.
            stop: The end time of the optimization horizon.
            steps_horizon_k: The number of time steps in the horizon.
            interval: The duration of each time step in minutes.
            norm_factor: A normalization factor for the objective function.

        Returns:
            A tuple containing the objective terms, constraints, and the dispatch
            variable for the CVXPY optimization problem.
        """

        # Retrieve space heating info as dictionaries
        start_time = time()
        space_heating_info = self._space_heating_retriever.retrieve_data(start, stop)
        execution_time = time() - start_time
        logger.info("The retrieval of space heating took %.2f seconds", execution_time)

        # Order devices using priorities
        devices = DeviceHelper.sort_devices_by_priorities(
            space_heating=True,
            electric_storage=False,
            electric_vehicle=False,
            water_heater=False,
        )
        thermal_zones_ordered = []
        for tz in devices:
            thermal_zones_ordered.append(tz["entity_id"])

        # Process data using the same order of devices as everywhere
        space_heating_arrays = self._process_data_as_arrays(
            space_heating_info, thermal_zones_ordered, steps_horizon_k
        )

        # Extract thermal model
        ax = space_heating_arrays["ax"]
        au = space_heating_arrays["au"]
        aw = space_heating_arrays["aw"]

        # Extract variables
        w_external_variables = space_heating_arrays["w_external_variables"]
        min_setpoint = space_heating_arrays["min_setpoint"]
        max_setpoint = space_heating_arrays["max_setpoint"]
        priorities = space_heating_arrays["priorities"]
        initial_state = space_heating_arrays["initial_state"]
        setpoint_preferences = space_heating_arrays["setpoint_preferences"]
        occupancy = space_heating_arrays["occupancy_preferences"]

        # Create indexes for the optimization
        quantity_of_thermal_zones = len(ax)
        quantity_of_heaters = len(au)

        # Create optimization variables
        x_temperature = cvx.Variable(
            (quantity_of_thermal_zones, steps_horizon_k),
            name="smart_thermostats_x_temperature",
        )
        u_heaters = cvx.Variable(
            (quantity_of_heaters, steps_horizon_k),
            nonneg=True,
            name="smart_thermostats_u_heaters",
        )

        # Define weights
        weights = priorities * occupancy

        # Define optimization objective
        objective = [
            cvx.sum(
                cvx.multiply(
                    ((setpoint_preferences - x_temperature) / norm_factor) ** 2, weights
                )
            )
            + 100
            * cvx.max(
                cvx.multiply(
                    cvx.abs(setpoint_preferences - x_temperature) / norm_factor, weights
                )
            )
        ]

        # Define optimization constraints
        constraints = []

        # Initial state of temperature by zone
        logger.debug("Initial measured temperature: %s", initial_state)
        constraints.append(x_temperature[:, 0] == initial_state)

        # Final state of temperature by zone
        # This constraint is too strict and should be included in the objective function
        # constraints.append(x_temperature[:, -1] == setpoint_preferences[:, -1])

        # Maximum output power of the heaters measured in kWh
        constraints.append(u_heaters <= 16.0 / quantity_of_thermal_zones)

        # Minimum and maximum temperature for the states
        constraints.append(x_temperature >= min_setpoint)
        constraints.append(x_temperature <= max_setpoint)

        # Constraint of power change in one interval
        constraints.append(
            cvx.abs(
                u_heaters[:, 1:steps_horizon_k] - u_heaters[:, 0 : steps_horizon_k - 1]
            )
            <= 2.0
        )

        # Thermal balance equation
        constraints.append(
            x_temperature[:, 1:steps_horizon_k]
            == cvx.matmul(ax, x_temperature[:, 0 : steps_horizon_k - 1])
            + cvx.matmul(au, u_heaters[:, 1:steps_horizon_k])
            + cvx.matmul(aw, w_external_variables[:, 1:steps_horizon_k])
        )

        # Define the electrical dispatch
        dispatch = cvx.sum(
            u_heaters, axis=0, keepdims=True
        )  # Always return an array with dimensions (1, steps_horizon_k)

        return objective, constraints, dispatch

    def _process_data_as_arrays(
        self,
        space_heating_info: Dict[str, Any],
        thermal_zones_ordered: List[str],
        steps_horizon_k: int,
    ) -> Dict[str, Any]:
        """Processes raw device data into NumPy arrays for the optimization model.

        This helper function converts the retrieved data for the space heating system
        into a structured dictionary of NumPy arrays suitable for the CVXPY model.
        It performs several key tasks:
        - Extracts the state-space model matrices (Ax, Au, Aw).
        - Assembles time-series data (weather, setpoints, occupancy) into matrices.
        - Ensures all data is correctly ordered according to the prioritized list
          of thermal zones.
        - Validates the initial temperature against comfort bounds and adjusts the
          bounds if necessary to prevent infeasible problems.
        - Verifies that all time-series data has the correct length for the horizon.

        Args:
            space_heating_info: A dictionary containing the raw data and parameters
                                   for the space heating system.
            thermal_zones_ordered: A list of thermal zone IDs, sorted by priority.
            steps_horizon_k: The number of time steps in the optimization horizon.

        Returns:
            A dictionary where keys are parameter names (e.g., 'ax', 'initial_state')
            and values are the corresponding NumPy arrays or matrices.
        """
        # Create space_heating_arrays
        space_heating_arrays = {}

        # Get Ax, Au, and Aw weights for the thermal model
        thermal_model = space_heating_info["thermal_model"]
        space_heating_arrays["ax"] = np.array(thermal_model["x_internal_states"])
        space_heating_arrays["au"] = np.array(thermal_model["u_heaters"])
        space_heating_arrays["aw"] = np.array(thermal_model["w_external_variables"])

        # Get the initial state of the thermal zones
        initial_state = space_heating_info["initial_state"]

        # Extract the minimum and maximum setpoints considering initial state
        # This build dynamic constraints for the optimization problem
        min_setpoint = {}
        max_setpoint = {}

        for room, state in initial_state.items():
            min_val = space_heating_info["min_setpoint"][room]
            max_val = space_heating_info["max_setpoint"][room]

            if state < min_val:
                logger.warning(
                    "Initial state for %s (%s) is lower than the minimum setpoint (%s). The minimum setpoint will be reduced to zero.",
                    room,
                    state,
                    min_val,
                )
                min_setpoint[room] = 0
            else:
                min_setpoint[room] = min_val

            if state > max_val:
                logger.warning(
                    "Initial state for %s (%s) is higher than the maximum setpoint (%s). The maximum setpoint will be increased to 30.",
                    room,
                    state,
                    max_val,
                )
                max_setpoint[room] = 30
            else:
                max_setpoint[room] = max_val

        priorities = space_heating_info["priority"]
        setpoint_preferences = space_heating_info["setpoint_preferences"]
        occupancy_preferences = space_heating_info["occupancy_preferences"]

        # Build the minimum setpoint array
        min_setpoint_array = np.array(
            [min_setpoint[k] for k in thermal_zones_ordered], dtype=float
        )
        if min_setpoint_array.ndim == 1 and min_setpoint_array.shape[0] == len(
            thermal_zones_ordered
        ):
            min_setpoint_matrix = np.tile(
                min_setpoint_array.reshape(-1, 1), (1, steps_horizon_k)
            )
            space_heating_arrays["min_setpoint"] = min_setpoint_matrix
        else:
            space_heating_arrays["min_setpoint"] = min_setpoint_array

        # Build the maximum setpoint array
        max_setpoint_array = np.array(
            [max_setpoint[k] for k in thermal_zones_ordered], dtype=float
        )
        if max_setpoint_array.ndim == 1 and max_setpoint_array.shape[0] == len(
            thermal_zones_ordered
        ):
            max_setpoint_matrix = np.tile(
                max_setpoint_array.reshape(-1, 1), (1, steps_horizon_k)
            )
            space_heating_arrays["max_setpoint"] = max_setpoint_matrix
        else:
            space_heating_arrays["max_setpoint"] = max_setpoint_array

        # Build the initial state array
        space_heating_arrays["initial_state"] = np.array(
            [initial_state[k] for k in thermal_zones_ordered], dtype=float
        )

        # Build the priorities array
        priorities_array = np.array(
            [priorities[k] for k in thermal_zones_ordered], dtype=float
        )
        space_heating_arrays["priorities"] = priorities_array.reshape(-1, 1)

        # Verify time index match
        weather_key = list(space_heating_info["weather_forecast"].keys())[0]
        weather_index = list(space_heating_info["weather_forecast"][weather_key].keys())
        setpoint_preferences_key = list(
            space_heating_info["setpoint_preferences"].keys()
        )[0]
        setpoint_preferences_index = list(
            space_heating_info["setpoint_preferences"][setpoint_preferences_key].keys()
        )
        occupancy_preferences_key = list(
            space_heating_info["occupancy_preferences"].keys()
        )[0]
        occupancy_preferences_index = list(
            space_heating_info["occupancy_preferences"][
                occupancy_preferences_key
            ].keys()
        )

        # Validate that all indexes are the same:
        if weather_index == setpoint_preferences_index == occupancy_preferences_index:
            logger.info(
                "Retrieved index for weather forecast and setpoint and occupancy preferences match."
            )
        else:
            logger.warning(
                "Retrieved index for weather forecast and setpoint and occupancy preferences are not the same."
            )

        # Create matrix W from weather forecasts
        weather_forecast_values = []
        for weather_measure in list(space_heating_info["weather_forecast"].keys()):
            forecast_measure = np.array(
                list(space_heating_info["weather_forecast"][weather_measure].values()),
                dtype=float,
            )
            weather_forecast_values.append(forecast_measure)
        # Clip weather
        len_weather = np.array(weather_forecast_values).shape[1]
        if len_weather == steps_horizon_k:
            space_heating_arrays["w_external_variables"] = np.array(
                weather_forecast_values
            )
        elif len_weather == steps_horizon_k + 1:
            # Delete last row of forecast
            space_heating_arrays["w_external_variables"] = np.array(
                weather_forecast_values
            )[:, :-1]
        else:
            logger.error(
                "Dimension of weather %s differs from needed %s",
                len_weather,
                steps_horizon_k,
            )

        # Build matrix for setpoint preferences
        setpoint_pref_values = []
        for zone in thermal_zones_ordered:
            array_per_zone = np.array(
                list(setpoint_preferences[zone].values()), dtype=float
            )
            setpoint_pref_values.append(array_per_zone)
        # Clip setpoints
        len_setpoint = np.array(setpoint_pref_values).shape[1]
        if len_setpoint == steps_horizon_k:
            space_heating_arrays["setpoint_preferences"] = np.array(
                setpoint_pref_values
            )
        elif len_setpoint == steps_horizon_k + 1:
            # Delete last row of forecast
            space_heating_arrays["setpoint_preferences"] = np.array(
                setpoint_pref_values
            )[:, :-1]
        else:
            logger.error(
                "Dimension of setpoints %s differs from needed %s",
                len_setpoint,
                steps_horizon_k,
            )

        # Build matrix for occupancy preferences
        occupancy_pref_values = []
        for zone in thermal_zones_ordered:
            array_per_zone = np.array(
                list(occupancy_preferences[zone].values()), dtype=float
            )
            occupancy_pref_values.append(array_per_zone)
        # Clip occupancy
        len_occupancy = np.array(occupancy_pref_values).shape[1]
        if len_occupancy == steps_horizon_k:
            space_heating_arrays["occupancy_preferences"] = np.array(
                occupancy_pref_values
            )
        elif len_occupancy == steps_horizon_k + 1:
            # Delete last row of forecast
            space_heating_arrays["occupancy_preferences"] = np.array(
                occupancy_pref_values
            )[:, :-1]
        else:
            logger.error(
                "Dimension of occupancy %s differs from needed %s",
                len_occupancy,
                steps_horizon_k,
            )

        return space_heating_arrays
