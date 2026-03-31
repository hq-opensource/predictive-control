"""This module defines the WaterHeaterMPC class, which models an electric water heater for MPC.

It extends the abstract DeviceMPC class, providing a concrete implementation
for formulating the optimization problem specific to controlling a water heater.
This includes defining objectives related to maintaining water temperature within
a desired range and incorporating constraints such as power limits, tank volume,
and thermal dynamics influenced by ambient temperature and water flow.
"""

from datetime import datetime, timedelta
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
            start, water_heater_info, steps_horizon_k, interval
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
        # nonneg=True is a hard physical floor (water cannot be < 0°C).
        # This is distinct from the soft comfort lower bound (min_temperature = 30°C):
        # the soft constraint allows slack, but temperature must remain physically valid.
        temperature = cvx.Variable(
            (1, steps_horizon_k + 1), nonneg=True, name="water_heater_temperature"
        )

        # Slack variables for soft temperature bounds — guarantee feasibility when
        # peak water draw cools the tank faster than the heater can compensate.
        slack_above = cvx.Variable(
            (1, steps_horizon_k + 1), nonneg=True, name="water_heater_slack_above"
        )
        slack_below = cvx.Variable(
            (1, steps_horizon_k + 1), nonneg=True, name="water_heater_slack_below"
        )

        # Define optimization objective
        # 1000× penalty on slack: violations are strongly discouraged but the
        # problem always has a feasible point even when capacity is insufficient.
        comfort_term = priority * cvx.sum(
            ((desired_state - temperature[:, :-1]) / norm_factor) ** 2
        )
        objective = [comfort_term + 1000 * cvx.sum(slack_above + slack_below)]

        # Constraints
        constraints: List[Any] = []

        # Initial state
        constraints.append(temperature[0, 0] == initial_state)

        # Soft temperature bounds
        constraints.append(temperature <= max_temperature + slack_above)
        constraints.append(temperature >= min_temperature - slack_below)

        # # Binary control: power = switch * power_capacity
        # constraints.append(power[0, :] == switch * power_capacity)
        constraints.append(power <= power_capacity)

        # Define ambient heat-loss conductance measured in W/°C
        ambient_heat_loss_conductance = 1.5 # W/°C
        
        # Dynamics
        # power is in kW; formula uses W-based constants (c in Wh/°C/L, V_tank in L,
        # delta_time in h) so multiply power by 1000 to convert kW → W equivalent.
        # water_flow is in L/h so c*water_flow has units W/°C, consistent with
        # the 2 W/°C ambient loss coefficient and the Wh denominator.
        constraints.append(
            temperature[0, 1 : steps_horizon_k + 1]
            == temperature[0, 0:steps_horizon_k]
            + (
                power * 1000  # kW → W equivalent for the thermal balance
                - cvx.multiply(
                    water_heater_constant * water_flow,
                    (temperature[0, 0:steps_horizon_k] - inlet_temperature),
                )
                - (temperature[0, 0:steps_horizon_k] - ambient_temperature) * ambient_heat_loss_conductance
            )
            * delta_time
            / (water_heater_constant * tank_volume)
        )

        # Dispatch
        dispatch = power

        # Warn when peak water draw exceeds heater capacity so operators know
        # the slack variables will absorb comfort violations during those steps.
        C_th = water_heater_constant * tank_volume
        max_heat_per_step = power_capacity * 1000 * delta_time / C_th
        max_flow_lh = float(np.max(water_flow))
        if max_flow_lh > 0:
            max_cool_per_step = (
                water_heater_constant
                * max_flow_lh
                * (initial_state - float(np.min(inlet_temperature)))
                * delta_time
                / C_th
            )
            if max_cool_per_step > max_heat_per_step:
                logger.warning(
                    "Peak water draw (%.1f L/min) cools tank at %.2f°C/step; "
                    "heater can only add %.2f°C/step. "
                    "Temperature comfort bound will be violated during high-draw periods.",
                    max_flow_lh / 60,
                    max_cool_per_step,
                    max_heat_per_step,
                )

        return objective, constraints, dispatch

    def _process_data_as_arrays(
        self,
        start: datetime,
        water_heater_info: Dict[str, Any],
        steps_horizon_k: int,
        interval: int = 10,
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
        # Load power capacity — device config is in kW, keep kW for MPC consistency
        water_heater_arrays["power_capacity"] = float(
            water_heater_info["power_capacity"][
                list(water_heater_info["power_capacity"].keys())[0]
            ]
        )  # kW
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

        # Load water flow — align consumption preferences to the horizon timestamps.
        # Nearest-timestamp matching (within 1 minute) is used instead of exact
        # equality so that minor timezone/rounding differences do not silently
        # drop the flow data and cause a KeyError downstream.
        wh_device_key = list(water_heater_info["consumption_preferences"].keys())[0]
        raw_flow_dict = water_heater_info["consumption_preferences"][wh_device_key]
        horizon_timestamps = [
            start + timedelta(minutes=i * interval) for i in range(steps_horizon_k)
        ]
        flow_values = []
        for ts in horizon_timestamps:
            best_key = min(
                raw_flow_dict.keys(),
                key=lambda k: abs((datetime.fromisoformat(k) - ts).total_seconds()),
            )
            diff_seconds = abs((datetime.fromisoformat(best_key) - ts).total_seconds())
            if diff_seconds <= 60:
                flow_values.append(raw_flow_dict[best_key])
            else:
                logger.warning(
                    "No water flow data within 1 minute of %s (closest gap: %.0fs). Using 0.0 L/min.",
                    ts,
                    diff_seconds,
                )
                flow_values.append(0.0)
        water_heater_arrays["water_flow"] = (
            np.array(flow_values).reshape(1, steps_horizon_k) * 60
        )  # Convert L/min to L/h

        # Fallback: guarantee water_flow is always set even if loading failed
        if "water_flow" not in water_heater_arrays:
            logger.warning("water_flow could not be loaded. Defaulting to zero hot water draw.")
            water_heater_arrays["water_flow"] = np.zeros((1, steps_horizon_k))

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
            water_heater_info["water_heater_constant"][
                list(water_heater_info["water_heater_constant"].keys())[0]
            ]
        )  # Wh/°C/Litre

        # Validate initial state against temperature bounds — log warnings but
        # do NOT weaken the bounds.  The soft constraints (slack variables with
        # 1000× penalty in the formulation) absorb the initial violation and
        # drive the optimizer to recover as fast as possible.
        if (
            water_heater_arrays["initial_state"]
            < water_heater_arrays["min_temperature"]
        ):
            logger.warning(
                "Initial state %.1f°C is lower than the minimum temperature %.1f°C. "
                "The soft constraint will absorb the initial violation; the optimizer "
                "will heat from the next step onward to restore the floor.",
                water_heater_arrays["initial_state"],
                water_heater_arrays["min_temperature"],
            )
        if (
            water_heater_arrays["initial_state"]
            > water_heater_arrays["max_temperature"]
        ):
            logger.warning(
                "Initial state %.1f°C is higher than the maximum temperature %.1f°C. "
                "The soft constraint will absorb the initial violation.",
                water_heater_arrays["initial_state"],
                water_heater_arrays["max_temperature"],
            )

        return water_heater_arrays
