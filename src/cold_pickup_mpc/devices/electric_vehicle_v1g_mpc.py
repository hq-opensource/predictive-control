"""This module defines the ElectricVehicleV1GMPC class, which models a V1G electric vehicle for MPC.

It extends the abstract DeviceMPC class, providing a concrete implementation
for formulating the optimization problem specific to unidirectional electric
vehicle charging. This includes defining objectives related to maintaining a
desired state of charge and incorporating constraints such as charging power
limits, battery capacity, and the vehicle's connection status.
"""

from datetime import datetime
from typing import Any, Dict, List, Tuple

import cvxpy as cvx
import numpy as np
import pandas as pd

from cold_pickup_mpc.devices.device_mpc import DeviceMPC
from cold_pickup_mpc.util.logging import LoggingUtil

logger = LoggingUtil.get_logger(__name__)


class ElectricVehicleV1GMPC(DeviceMPC):
    """Represents a V1G (unidirectional charging) Electric Vehicle for the MPC.

    This class models an electric vehicle that can only draw power from the grid
    (V1G - Vehicle-to-Grid unidirectional). It formulates an optimization problem
    to control the EV's charging schedule based on its availability (i.e., when it
    is plugged in) and charging preferences, while respecting the vehicle's
    battery constraints.
    """

    def __init__(
        self,
        device_info: List[Dict[str, Any]],
    ) -> None:
        """Initializes the ElectricVehicleV1GMPC.

        Args:
            device_info: A list containing a single dictionary with the configuration
                         and parameters of the electric vehicle.
        """
        super().__init__(device_info)
        # Extract info of the unique device
        device_dict = device_info[0]
        self.device_dict = device_dict
        self._energy_capacity = float(device_dict["energy_capacity"])  # Wh
        self._power_capacity = float(device_dict["power_capacity"])  # W
        self._charging_efficiency = float(device_dict.get("charging_efficiency", 0.99))
        self._min_residual_energy = float(
            device_dict.get("min_residual_energy", 25)
        )  # %
        self._max_residual_energy = float(
            device_dict.get("max_residual_energy", 95)
        )  # %
        self._decay_factor = float(
            device_dict.get("decay_factor", 0.99)
        )  # Optional, default 1

    def create_mpc_formulation(
        self,
        start: datetime,
        stop: datetime,
        interval: int,
        v1g_info: Dict[str, pd.DataFrame],
    ) -> Tuple[List[Any], List[Any], cvx.Variable]:
        """Creates the optimization formulation for the V1G electric vehicle.

        This method builds a CVXPY optimization problem that determines the optimal
        charging schedule for the EV. The objective is to minimize the deviation
        from a desired state of charge. The model includes constraints for:
        - SoC limits (min and max).
        - Charging power limits.
        - The EV's connection status (it can only charge when plugged in, as
          indicated by the `branched_profile`).
        - The energy balance equation for the battery.

        Args:
            start: The start time of the optimization horizon.
            stop: The end time of the optimization horizon.
            interval: The duration of each time step in minutes.
            v1g_info: A dictionary containing DataFrames for the 'initial_state'
                      and 'branched_profile' (connection status) of the EV.

        Returns:
            A tuple containing the objective terms, constraints, and the dispatch
            variable for the CVXPY optimization problem.

        Raises:
            ValueError: If the input data (e.g., `branched_profile`, `initial_state`)
                        has incorrect dimensions or values.
        """
        # Create external variables
        initial_state = v1g_info["initial_state"]
        branched_profile = v1g_info["branched_profile"]

        # Define simulation values
        # Validate input timestamps
        if stop < start:
            logger.error(
                "Invalid timestamps: stop time must be greater than start time."
            )
            raise ValueError("stop time must be greater than start time.")

        # Compute number of steps for the computed time
        timespan = (
            stop - start
        ).total_seconds() / 60  # Convert time difference to minutes
        steps_horizon_k = int(
            np.ceil(timespan / interval)
        )  # Ceiling to get the upper integer
        delta_time = 1 / (60 / interval)

        # Validate inputs
        branched = branched_profile.to_numpy().flatten()
        if len(branched) != steps_horizon_k:
            raise ValueError("branched_profile length must match time horizon.")
        if not np.all(np.isin(branched, [0, 1])):
            raise ValueError("branched_profile must contain only 0s and 1s.")
        init_val = initial_state.to_numpy().flatten()
        if init_val.size != 1:
            raise ValueError("initial_state must be a single value.")

        # Define optimization variables
        switch = cvx.Variable(
            steps_horizon_k, boolean=True, name="electric_vehicle_switch"
        )
        charge_power = cvx.Variable(
            (1, steps_horizon_k), nonneg=True, name="electric_vehicle_charge_power"
        )
        residual_energy = cvx.Variable(
            (1, steps_horizon_k + 1),
            nonneg=True,
            name="electric_vehicle_residual_energy",
        )

        # Define optimization objective
        priority = float(self.device_dict["priority"])
        norm_factor = float(
            self.device_dict.get("norm_factor", self._energy_capacity)
        )  # The use of residual energy allows to use capacity as normalization factor
        desired_soc = (
            float(self.device_dict.get("desired_state", 90))
            / 100
            * self._energy_capacity
        )
        desired_state = desired_soc * np.ones((1, steps_horizon_k))
        comfort_term = priority * cvx.sum_squares(
            (desired_state - residual_energy[:, :-1]) / norm_factor
        )
        objective = [comfort_term]

        # Define constraints
        constraints: List = []

        # State constraints
        constraints.append(
            residual_energy <= self._max_residual_energy / 100 * self._energy_capacity
        )
        constraints.append(
            residual_energy >= self._min_residual_energy / 100 * self._energy_capacity
        )
        constraints.append(residual_energy[0, 0] == init_val[0])
        if "final_soc_requirement" in self.device_dict:
            constraints.append(
                residual_energy[0, -1]
                >= self.device_dict["final_soc_requirement"]
                / 100
                * self._energy_capacity
            )

        # Charging logic: charge_power = switch * branched_profile * max_power
        constraints.append(
            charge_power[0, :] == switch * self._power_capacity * branched
        )
        constraints.append(
            charge_power <= self._power_capacity
        )  # Redundant but ensures bounds

        # Balance equation
        constraints.append(
            residual_energy[0, 1 : steps_horizon_k + 1]
            == self._decay_factor * residual_energy[0, 0:steps_horizon_k]
            + cvx.multiply(
                self._charging_efficiency * delta_time,
                charge_power[0, 0:steps_horizon_k],
            )
        )

        # Add the dispatch variable
        dispatch = charge_power

        return objective, constraints, dispatch
