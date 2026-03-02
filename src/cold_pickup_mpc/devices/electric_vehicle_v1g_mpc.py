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
    to control the EV's charging schedule with continuous power modulation based on 
    its availability (i.e., when it is plugged in) and charging preferences, while 
    respecting the vehicle's battery constraints. The control uses a continuous 
    variable (0-1) allowing for precise power adjustment rather than simple on/off control.
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
        super().__init__()
        # Extract info of the unique device
        device_dict = device_info[0]
        self.device_dict = device_dict
        self._energy_capacity = float(device_dict["energy_capacity"])  # Wh
        self._power_capacity = float(device_dict["power_capacity"])  # W
        self._charging_efficiency = float(device_dict.get("charging_efficiency") or 0.99)
        self._min_residual_energy = float(
            device_dict.get("min_residual_energy") or 25)  # %
        self._max_residual_energy = float(
            device_dict.get("max_residual_energy") or 95)  # %
        self._decay_factor = float(
            device_dict.get("decay_factor", 0.99))  # Optional, default 1
        self._max_power_ramp_rate = float(
            device_dict.get("max_power_ramp_rate", 0.2))  # Maximum change in switch variable per time step (default 20%/step)
        self._enable_ramping = bool(
            device_dict.get("enable_ramping", True))  # Enable/disable power ramping constraints

    def create_mpc_formulation(
        self,
        start: datetime,
        stop: datetime,
        interval: int,
        v1g_info: Dict[str, pd.DataFrame],
    ) -> Tuple[List[Any], List[Any], cvx.Variable]:
        """Creates the optimization formulation for the V1G electric vehicle.

        This method builds a CVXPY optimization problem that determines the optimal
        charging schedule for the EV with continuous power control. The objective is to 
        minimize the deviation from a desired state of charge. The model includes constraints for:
        - SoC limits (min and max).
        - Continuous charging power control (0-100% of max power).
        - Optional power ramping constraints for smoother transitions.
        - The EV's connection status (it can only charge when plugged in, as
          indicated by the `branched_profile`).
        - The energy balance equation for the battery.
        - Enhanced input validation and error handling.

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

        logger.debug(f"Creating EV MPC formulation: {start} to {stop}, interval={interval}min")
        logger.debug(f"EV parameters: capacity={self._energy_capacity}Wh, power={self._power_capacity}W")
        logger.debug(f"Ramping enabled: {self._enable_ramping}, max_ramp_rate: {self._max_power_ramp_rate}")

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
            logger.error(f"branched_profile length {len(branched)} does not match time horizon {steps_horizon_k}")
            raise ValueError("branched_profile length must match time horizon.")
        if not np.all(np.isin(branched, [0, 1])):
            logger.error("branched_profile contains invalid values (must be 0 or 1)")
            raise ValueError("branched_profile must contain only 0s and 1s.")
        init_val = initial_state.to_numpy().flatten()
        if init_val.size != 1:
            logger.error(f"initial_state has {init_val.size} values, expected 1")
            raise ValueError("initial_state must be a single value.")
        if init_val[0] < 0 or init_val[0] > self._energy_capacity:
            logger.error(f"initial_state {init_val[0]} is outside valid range [0, {self._energy_capacity}]")
            raise ValueError(f"initial_state must be between 0 and {self._energy_capacity} Wh.")

        # Define optimization variables
        switch = cvx.Variable(
            steps_horizon_k, nonneg=True, name="electric_vehicle_switch"
        ) # Continuous between 0 and 1
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
            float(self.device_dict.get("desired_state") or 90)
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

        # Switch bounds (continuous control between 0 and 1)
        constraints.append(switch <= 1.0)

        # Power ramping constraints (optional, for smoother power transitions)
        if self._enable_ramping and steps_horizon_k > 1:
            # Limit the rate of change in the switch variable
            for k in range(steps_horizon_k - 1):
                constraints.append(
                    switch[k + 1] - switch[k] <= self._max_power_ramp_rate
                )
                constraints.append(
                    switch[k] - switch[k + 1] <= self._max_power_ramp_rate
                )

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

    def _process_data_as_arrays(
        self, electric_vehicle_info: Dict[str, Any], steps_horizon_k: int
    ) -> Dict[str, np.ndarray]:
        """Processes raw device data into NumPy arrays for the optimization model.

        This helper function takes the dictionary of data retrieved for the electric
        storage device and converts it into a structured dictionary of NumPy arrays.
        This format is required by the CVXPY optimization problem. It handles unit
        conversions (e.g., SoC from % to kWh) and validates the initial state
        against the defined SoC limits.

        Args:
            electric_vehicle_info: A dictionary containing the raw data and parameters
                                   for the electric storage device.
            steps_horizon_k: The number of time steps in the optimization horizon.

        Returns:
            A dictionary where keys are parameter names (e.g., 'initial_state',
            'power_capacity') and values are the corresponding NumPy arrays.
        """

        static_properties: Dict[str, Dict[str, Any]] = {
            "priority": {"type": int, "default": 13},
            "critical_state": {"type": float, "default": 20.0},
            "desired_state": {"type": float, "default": 90.0},
            "power_capacity": {"type": float, "default": 4.5},
            "critical_action": {"type": float, "default": 0.0},
            "activation_action": {"type": float, "default": 4.5},
            "deactivation_action": {"type": float, "default": 0.0},
            "modulation_capability": {"type": bool, "default": True},
            "discharge_capability": {"type": bool, "default": True},
            "energy_capacity": {"type": float, "default": 75},
            "charging_efficiency": {"type": float, "default": 0.98},
            "discharging_efficiency": {"type": float, "default": 0.98},
            "min_residual_energy": {"type": float, "default": 30},
            "max_residual_energy": {"type": float, "default": 95},
            "decay_factor": {"type": float, "default": 0.995},
        }

        electric_storage_arrays = {}
        # Energy capacity of the battery
        energy_capacity = electric_vehicle_info["energy_capacity"]["battery"]
        electric_storage_arrays["energy_capacity"] = energy_capacity

        # Initial state of the battery
        initial_state = (
            electric_vehicle_info["initial_state"]["battery"]
            / 100
            * electric_storage_arrays["energy_capacity"]
        )
        electric_storage_arrays["initial_state"] = initial_state

        # Minimum and maximum residual energy of the battery
        min_residual_energy = (
            electric_vehicle_info["min_residual_energy"]["battery"]
            / 100
            * energy_capacity
        )
        max_residual_energy = (
            electric_vehicle_info["max_residual_energy"]["battery"]
            / 100
            * energy_capacity
        )
        if initial_state > max_residual_energy:
            logger.warning(
                "Initial state of charge of the battery %s kWh is greater than maximum residual energy %s kWh.",
                initial_state,
                max_residual_energy,
            )
            logger.warning(
                "Setting max_residual_energy to total energy capacity of the battery."
            )
            max_residual_energy = energy_capacity
        if initial_state < min_residual_energy:
            logger.warning(
                "Initial state of charge of the battery %s kWh is less than minimum residual energy %s kWh.",
                initial_state,
                min_residual_energy,
            )
            logger.warning("Setting min_residual_energy of the battery to zero.")
            min_residual_energy = energy_capacity
        electric_storage_arrays["min_residual_energy"] = min_residual_energy
        electric_storage_arrays["max_residual_energy"] = max_residual_energy

        # Desired state of the battery
        electric_storage_arrays["desired_state"] = (
            electric_vehicle_info["desired_state"]["battery"] / 100 * energy_capacity
        )

        # Priority of the battery
        electric_storage_arrays["priority"] = electric_vehicle_info["priority"][
            "battery"
        ]

        # Final state of charge requirement of the battery
        electric_storage_arrays["final_soc_requirement"] = (
            electric_vehicle_info["final_soc_requirement"]["battery"]
            / 100
            * electric_storage_arrays["energy_capacity"]
        )

        # Other variables
        electric_storage_arrays["power_capacity"] = electric_vehicle_info[
            "power_capacity"
        ]["battery"]
        electric_storage_arrays["decay_factor"] = electric_vehicle_info["decay_factor"][
            "battery"
        ]
        electric_storage_arrays["charging_efficiency"] = electric_vehicle_info[
            "charging_efficiency"
        ]["battery"]
        electric_storage_arrays["discharging_efficiency"] = electric_vehicle_info[
            "discharging_efficiency"
        ]["battery"]
        electric_storage_arrays["norm_factor"] = electric_vehicle_info[
            "energy_capacity"
        ]["battery"]

        return electric_storage_arrays
