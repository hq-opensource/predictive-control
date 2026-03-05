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
from cold_pickup_mpc.retrievers.electric_vehicle_v1g_retriever import (
    ElectricVehicleV1gDataRetriever,
)
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
        devices: List[Dict[str, Any]],
    ) -> None:
        """Initializes the ElectricVehicleV1GMPC.

        Args:
            devices: A list containing dictionaries with the configuration
                         and parameters of the electric vehicles.
        """
        super().__init__()
        self._electric_vehicle_retriever = ElectricVehicleV1gDataRetriever(devices)
        # Extract info of the unique device (current implementation handles one EV)
        device_dict = devices[0]
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
        steps_horizon_k: int,
        interval: int = 10,
        norm_factor: int = 10,
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
        # Retrieve data
        v1g_info = self._electric_vehicle_retriever.retrieve_data(start, stop)

        # Build dynamic constraints for the optimization problem
        v1g_arrays = self._process_data_as_arrays(v1g_info, steps_horizon_k)

        # Create external variables
        initial_state = v1g_arrays["initial_state"]
        branched_profile = v1g_arrays["branched_profile"]
        min_residual_energy = v1g_arrays["min_residual_energy"]
        max_residual_energy = v1g_arrays["max_residual_energy"]
        decay_factor = v1g_arrays["decay_factor"]

        logger.debug(f"Creating EV MPC formulation: {start} to {stop}, interval={interval}min")
        logger.debug(f"EV parameters: capacity={self._energy_capacity}Wh, power={self._power_capacity}W")
        logger.debug(f"Ramping enabled: {self._enable_ramping}, max_ramp_rate: {self._max_power_ramp_rate}")

        delta_time = 1 / (60 / interval)

        # Validate inputs
        # Validate inputs
        if len(branched_profile) != steps_horizon_k:
            logger.error(f"branched_profile length {len(branched_profile)} does not match time horizon {steps_horizon_k}")
            raise ValueError("branched_profile length must match time horizon.")
        if not np.all(np.isin(branched_profile, [0, 1])):
            logger.error("branched_profile contains invalid values (must be 0 or 1)")
            raise ValueError("branched_profile must contain only 0s and 1s.")
        if initial_state < 0 or initial_state > self._energy_capacity:
            logger.error(f"initial_state {initial_state} is outside valid range [0, {self._energy_capacity}]")
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
            residual_energy <= max_residual_energy / 100 * self._energy_capacity
        )
        constraints.append(
            residual_energy >= min_residual_energy / 100 * self._energy_capacity
        )
        constraints.append(residual_energy[0, 0] == initial_state)
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
            == decay_factor * residual_energy[0, 0:steps_horizon_k]
            + cvx.multiply(
                self._charging_efficiency * delta_time,
                charge_power[0, 0:steps_horizon_k],
            )
        )

        # Branched constraint (only charge when plugged in)
        constraints.append(
            charge_power[0, :] <= cvx.multiply(branched_profile, self._power_capacity)
        )

        # Switch constraint (continuous control)
        constraints.append(
            charge_power[0, :] <= cvx.multiply(switch, self._power_capacity)
        )

        # Add the dispatch variable
        dispatch = charge_power

        return objective, constraints, dispatch

    def _process_data_as_arrays(
        self, v1g_info: Dict[str, Any], steps_horizon_k: int
    ) -> Dict[str, Any]:
        """Processes raw device data into NumPy arrays for the optimization model.

        This helper function takes the dictionary of data retrieved for the electric
        vehicle and converts it into a structured dictionary of NumPy arrays.

        Args:
            v1g_info: A dictionary containing the raw data and parameters
                                   for the electric vehicle.
            steps_horizon_k: The number of time steps in the optimization horizon.

        Returns:
            A dictionary where keys are parameter names (e.g., 'initial_state',
            'branched_profile') and values are the corresponding NumPy arrays.
        """
        entity_id = self.device_dict["entity_id"]
        v1g_arrays = {}

        # 1. Energy capacity (assume static property, fetched via retriever)
        energy_capacity = v1g_info["energy_capacity"][entity_id]
        v1g_arrays["energy_capacity"] = energy_capacity

        # 2. Initial state
        raw_initial_state = v1g_info["initial_state"][entity_id]
        # If the state is a dictionary, extract the specific field (usually 'soc')
        if isinstance(raw_initial_state, dict):
            # Try some common field names if not explicitly specified
            initial_soc = raw_initial_state.get("soc")
            if initial_soc is None:
                 initial_soc = raw_initial_state.get("battery_soc", 50.0)
        else:
            initial_soc = raw_initial_state
            
        initial_state_wh = (initial_soc / 100 * energy_capacity)
        v1g_arrays["initial_state"] = initial_state_wh

        # 3. Min/Max residual energy
        min_residual_energy = v1g_info["min_residual_energy"][entity_id]
        max_residual_energy = v1g_info["max_residual_energy"][entity_id]

        if initial_soc > max_residual_energy:
            logger.warning(
                "Initial SoC of EV %s (%s%%) is greater than max_residual_energy (%s%%). Adjusting max.",
                entity_id, initial_soc, max_residual_energy
            )
            max_residual_energy = initial_soc
        if initial_soc < min_residual_energy:
            logger.warning(
                "Initial SoC of EV %s (%s%%) is less than min_residual_energy (%s%%). Adjusting min to slightly below initial.",
                entity_id, initial_soc, min_residual_energy
            )
            min_residual_energy = max(0, initial_soc - 0.1) # Slack for feasibility
        
        v1g_arrays["min_residual_energy"] = min_residual_energy
        v1g_arrays["max_residual_energy"] = max_residual_energy

        # 4. Decay factor
        v1g_arrays["decay_factor"] = v1g_info["decay_factor"][entity_id]

        # 5. Branched profile (connection status)
        raw_branched = v1g_info["branched_preferences"][entity_id]
        if isinstance(raw_branched, dict) and "forecast" in raw_branched:
             branched_dict = raw_branched["forecast"]
        else:
             branched_dict = raw_branched
             
        branched_values = np.array(list(branched_dict.values()), dtype=float)[:steps_horizon_k]
        v1g_arrays["branched_profile"] = branched_values

        return v1g_arrays
