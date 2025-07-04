from datetime import datetime
from typing import Any, Dict, List, Tuple

import cvxpy as cvx
import numpy as np

from cold_pickup_mpc.devices.device_mpc import DeviceMPC
from cold_pickup_mpc.retrievers.water_heater_retriever import WaterHeaterDataRetriever
from cold_pickup_mpc.util.logging import LoggingUtil

logger = LoggingUtil.get_logger(__name__)


class WaterHeaterMPC(DeviceMPC):
    """Represents a water heater for the MPC.

    This class models the thermal behavior of an electric water heater. It
    formulates an optimization problem to control the heater's power consumption
    to maintain the water temperature within a desired range, while considering
    hot water usage, heat losses, and system constraints.
    """

    def __init__(
        self,
        devices: List[Dict[str, Any]],
    ) -> None:
        """Initializes the WaterHeaterMPC.

        Args:
            devices: A list of dictionaries, where each dictionary contains the
                     configuration and parameters of a water heater device.
        """
        # Create the data retriever
        self._water_heater_retriever = WaterHeaterDataRetriever(devices)

    def create_mpc_formulation(
        self,
        start: datetime,
        stop: datetime,
        steps_horizon_k: int,
        interval: int = 10,
        norm_factor: int = 50,  # Default 50°K
    ) -> Tuple[List[Any], List[Any], cvx.Variable]:
        """Creates the optimization formulation for the water heater.

        This method constructs a CVXPY optimization problem based on a thermal
        model of the water heater tank. The objective is to minimize deviations
        from a desired temperature setpoint. The model includes constraints for:
        - The thermal dynamics of the water tank, accounting for heating,
          heat loss to the ambient environment, and hot water draws.
        - Temperature limits (min and max).
        - Maximum power output of the heating element.

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

        # Retrieve water heater info as dictionaries
        water_heater_info = self._water_heater_retriever.retrieve_data(start, stop)

        # Process data as arrays
        water_heater_arrays = self._process_data_as_arrays(
            start, water_heater_info, steps_horizon_k
        )

        # Compute delta time
        delta_time = interval / 60  # Convert to hours for power (W) to energy (Wh)

        # Create external variables
        initial_state = water_heater_arrays["initial_state"]
        ambient_temperature = water_heater_arrays["ambient_temperature"]  # T_a
        water_flow = water_heater_arrays["water_flow"]  # V_dsot
        inlet_temperature = water_heater_arrays["inlet_temperature"]  # X_inlet
        min_temperature = water_heater_arrays["min_temperature"]  # T_min
        max_temperature = water_heater_arrays["max_temperature"]  # T_max
        tank_volume = water_heater_arrays["tank_volume"]  # V_tank
        priority = water_heater_arrays["priority"]
        desired_state = water_heater_arrays["desired_state"]  # Default 80°C
        power_capacity = water_heater_arrays["power_capacity"]  # P_max
        water_heater_constant = water_heater_arrays[
            "water_heater_constant"
        ]  # Constant from Francois

        # Define variables
        # switch = cvx.Variable(steps_horizon_k, boolean=True, name="water_heater_switch")
        power = cvx.Variable(
            (1, steps_horizon_k), nonneg=True, name="water_heater_power"
        )
        temperature = cvx.Variable(
            (1, steps_horizon_k + 1), nonneg=True, name="water_heater_temperature"
        )

        # Define optimization objective
        comfort_term = priority * cvx.sum(
            ((desired_state - temperature[:, :-1]) / norm_factor) ** 2
        )
        objective = [comfort_term]

        # Constraints
        constraints: List[Any] = []

        # Initial state
        constraints.append(temperature[0, 0] == initial_state)

        # State limits
        constraints.append(temperature >= min_temperature)
        constraints.append(temperature <= max_temperature)

        # # Binary control: power = switch * power_capacity
        # constraints.append(power[0, :] == switch * power_capacity)
        constraints.append(power <= power_capacity)

        # Dynamics
        constraints.append(
            temperature[0, 1 : steps_horizon_k + 1]
            == temperature[0, 0:steps_horizon_k]
            + (
                power
                - cvx.multiply(
                    water_heater_constant * water_flow,
                    (temperature[0, 0:steps_horizon_k] - inlet_temperature),
                )
                - (temperature[0, 0:steps_horizon_k] - ambient_temperature) * 2
            )
            * delta_time
            / (water_heater_constant * tank_volume)
        )

        # # Dynamics
        # constraints.append(
        #     temperature[0, 1 : steps_horizon_k + 1]
        #     == temperature[0, 0:steps_horizon_k]
        #     + (
        #         (power / thermal_capacitance)
        #         + (thermal_conductance / thermal_capacitance)
        #         * (ambient_temperature - temperature[0, 0:steps_horizon_k])
        #         - cvx.multiply((water_flow / tank_volume), (temperature[0, 0:steps_horizon_k] - inlet_temperature))
        #     )
        #     * delta_time
        #     * 3600  # Convert hours to seconds for J/K consistency
        # )

        # Dispatch
        dispatch = power

        return objective, constraints, dispatch

    def _process_data_as_arrays(
        self,
        start: datetime,
        water_heater_info: Dict[str, Any],
        steps_horizon_k: int,
    ) -> Dict[str, Any]:
        """Processes raw device data into NumPy arrays for the optimization model.

        This helper function converts the retrieved data for the water heater
        into a structured dictionary of NumPy arrays suitable for the CVXPY model.
        It handles:
        - Extraction of static parameters (e.g., tank volume, power capacity).
        - Conversion of time-series data (e.g., water flow, ambient temperature)
          into NumPy arrays with the correct length for the optimization horizon.
        - Validation of the initial temperature against the operational temperature
          limits, adjusting them if necessary to ensure a feasible problem.
        - Unit conversions (e.g., power from kW to W, water flow from L/min to m³/s).

        Args:
            start: The start time of the optimization horizon.
            water_heater_info: A dictionary containing the raw data and parameters
                               for the water heater.
            steps_horizon_k: The number of time steps in the optimization horizon.

        Returns:
            A dictionary where keys are parameter names (e.g., 'initial_state',
            'power_capacity') and values are the corresponding NumPy arrays.
        """
        # Create water_heater_arrays
        water_heater_arrays = {}

        # Load priorities
        water_heater_arrays["priority"] = float(
            water_heater_info["priority"][list(water_heater_info["priority"].keys())[0]]
        )
        # Load desired state
        water_heater_arrays["desired_state"] = (
            water_heater_info["desired_state"][
                list(water_heater_info["desired_state"].keys())[0]
            ]
        ) * np.ones((1, steps_horizon_k))
        # Load initial state
        water_heater_arrays["initial_state"] = float(
            water_heater_info["initial_state"][
                list(water_heater_info["initial_state"].keys())[0]
            ]
        )
        # Load power capacity
        water_heater_arrays["power_capacity"] = float(
            water_heater_info["power_capacity"][
                list(water_heater_info["power_capacity"].keys())[0]
            ]
            * 1000  # Convert to W
        )
        # Load tank_volume
        water_heater_arrays["tank_volume"] = float(
            water_heater_info["tank_volume"][
                list(water_heater_info["tank_volume"].keys())[0]
            ]
        )  # Default: 270 L

        # Load inlet_temperature
        inlet_temperature = water_heater_info["inlet_temperature"][
            list(water_heater_info["inlet_temperature"].keys())[0]
        ]
        water_heater_arrays["inlet_temperature"] = np.full(
            (1, steps_horizon_k), inlet_temperature
        )  # Default: 16°C

        # Load dynamic data
        # Load ambient temperature
        ambient_temperature = water_heater_info["ambient_temperature"][
            list(water_heater_info["ambient_temperature"].keys())[0]
        ]
        water_heater_arrays["ambient_temperature"] = np.full(
            (1, steps_horizon_k), ambient_temperature
        )

        # Load water flow
        # Get the first timestamp key from the nested dict
        first_key = list(
            list(water_heater_info["consumption_preferences"].values())[0].keys()
        )[0]
        # Parse the ISO 8601 timestamp string into a datetime object
        first_datetime = datetime.fromisoformat(first_key)
        if first_datetime == start:
            # If the first timestamp matches the start time, use the corresponding value
            water_flow = np.array(
                list(
                    water_heater_info["consumption_preferences"][
                        list(water_heater_info["consumption_preferences"].keys())[0]
                    ].values()
                )[0:steps_horizon_k]
            ).reshape(1, steps_horizon_k)
            water_heater_arrays["water_flow"] = (
                water_flow * (1 / 1000) / 60
            )  # Convert to m^3/s
        else:
            logger.error(
                "start time %s not equal to the first timestamp %s in the water heater consumption preferences",
                start,
                first_datetime,
            )

        # Check if all arrays have the same length
        if not all(
            arr.shape[1] == steps_horizon_k
            for arr in [
                water_heater_arrays["ambient_temperature"],
                water_heater_arrays["water_flow"],
                water_heater_arrays["inlet_temperature"],
            ]
        ):
            logger.error("External input DataFrames must match time horizon length.")
        else:
            logger.debug("External input DataFrames match time horizon length.")

        # Load min_temperature constraint
        water_heater_arrays["min_temperature"] = float(
            water_heater_info["min_temperature"][
                list(water_heater_info["min_temperature"].keys())[0]
            ]
        )  # Default: 30°C
        # Load max_temperature constraint
        water_heater_arrays["max_temperature"] = float(
            water_heater_info["max_temperature"][
                list(water_heater_info["max_temperature"].keys())[0]
            ]
        )  # Default: 90°C
        # Load water heater constant
        water_heater_arrays["water_heater_constant"] = float(
            water_heater_info["max_temperature"][
                list(water_heater_info["water_heater_constant"].keys())[0]
            ]
        )  # Wh/°C/Litre

        # Add dynamic constraints for the water heater veryfing against the inital state
        if (
            water_heater_arrays["initial_state"]
            < water_heater_arrays["min_temperature"]
        ):
            logger.error(
                "Initial state %s is lower than the minimum temperature %s",
                water_heater_arrays["initial_state"],
                water_heater_arrays["min_temperature"],
            )
            water_heater_arrays["min_temperature"] = (
                0  # Set to 0 to avoid violating constraints
            )
        if (
            water_heater_arrays["initial_state"]
            > water_heater_arrays["max_temperature"]
        ):
            logger.error(
                "Initial state %s is higher than the maximum temperature %s",
                water_heater_arrays["initial_state"],
                water_heater_arrays["max_temperature"],
            )
            water_heater_arrays["max_temperature"] = (
                100  # Set to 100°C to avoid violating constraints
            )

        return water_heater_arrays
