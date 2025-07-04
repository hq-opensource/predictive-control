from datetime import datetime
from typing import Any, Dict, List, Tuple

import cvxpy as cvx
import numpy as np

from cold_pickup_mpc.devices.device_mpc import DeviceMPC
from cold_pickup_mpc.retrievers.electric_storage_retriever import (
    ElectricStorageDataRetriever,
)
from cold_pickup_mpc.util.logging import LoggingUtil

logger = LoggingUtil.get_logger(__name__)


class ElectricStorageMPC(DeviceMPC):
    """Represents an electric storage device (e.g., a battery) for the MPC.

    This class models the behavior of a stationary battery energy storage system (BESS).
    It formulates the optimization problem for charging and discharging the battery
    to meet certain objectives (e.g., maintaining a desired state of charge) while
    respecting the physical limitations of the device.
    """

    def __init__(
        self,
        devices: List[Dict[str, Any]],
    ) -> None:
        """Initializes the ElectricStorageMPC.

        Args:
            devices: A list of dictionaries, where each dictionary contains the
                     configuration and parameters of an electric storage device.
        """
        self._space_heating_retriever = ElectricStorageDataRetriever(devices)

    def create_mpc_formulation(
        self,
        start: datetime,
        stop: datetime,
        steps_horizon_k: int,
        interval: int = 10,
        norm_factor: int = 10,
    ) -> Tuple[List[Any], List[Any], cvx.Variable]:
        """Creates the optimization formulation for the electric storage device.

        This method builds a CVXPY optimization problem that models the battery's
        behavior over the prediction horizon. The objective is to minimize the deviation
        from a desired state of charge, while adhering to constraints such as:
        - State of charge (SoC) limits (min and max).
        - Charging and discharging power limits.
        - The energy balance equation that governs how SoC changes over time.

        Args:
            start: The start time of the optimization horizon.
            stop: The end time of the optimization horizon.
            steps_horizon_k: The number of time steps in the horizon.
            interval: The duration of each time step in minutes.
            norm_factor: A normalization factor for the objective function.

        Returns:
            A tuple containing the objective terms, constraints, and the dispatch variable
            for the CVXPY optimization problem.
        """

        # Compute delta time
        delta_time = 1 / (60 / interval)

        # Retrieve data
        electric_storage_info = self._space_heating_retriever.retrieve_data(start, stop)

        # Load external variables
        electric_storage_arrays = self._process_data_as_arrays(
            electric_storage_info, steps_horizon_k
        )
        initial_state = electric_storage_arrays["initial_state"]
        desired_state = electric_storage_arrays["desired_state"]
        energy_capacity = electric_storage_arrays["energy_capacity"]
        priority = electric_storage_arrays["priority"]
        final_soc_requirement = electric_storage_arrays["final_soc_requirement"]
        min_residual_energy = electric_storage_arrays["min_residual_energy"]
        max_residual_energy = electric_storage_arrays["max_residual_energy"]
        power_capacity = electric_storage_arrays["power_capacity"]
        decay_factor = electric_storage_arrays["decay_factor"]
        charging_efficiency = electric_storage_arrays["charging_efficiency"]
        discharging_efficiency = electric_storage_arrays["discharging_efficiency"]
        norm_factor = electric_storage_arrays["norm_factor"]

        # Validate input timestamps
        if stop < start:
            logger.error(
                "Invalid timestamps: stop time must be greater than start time."
            )
            raise ValueError("stop time must be greater than start time.")

        # Define optimization variables
        charge_power = cvx.Variable(
            (1, steps_horizon_k), nonneg=True, name="electric_storage_charge_power"
        )
        discharge_power = cvx.Variable(
            (1, steps_horizon_k), nonneg=True, name="electric_storage_discharge_power"
        )
        residual_energy = cvx.Variable(
            (1, steps_horizon_k + 1),
            nonneg=True,
            name="electric_storage_residual_energy",
        )

        # Define optimization objective
        desired_state_array = desired_state * np.ones(
            (1, steps_horizon_k)
        )  # Constant desired SoC
        comfort_term = priority * cvx.sum(
            ((desired_state_array - residual_energy[:, :-1]) / norm_factor) ** 2
        )
        objective = [comfort_term]

        # Define optimization constraints
        constraints: List = []

        # Maxium and minimum residual energy of the battery ()
        constraints.append(residual_energy <= max_residual_energy)
        constraints.append(residual_energy >= min_residual_energy)

        # Initial and final state of the battery
        constraints.append(residual_energy[0, 0] == initial_state)
        constraints.append(residual_energy[0, -1] >= final_soc_requirement)

        # Maximum charge and discharge per time step
        constraints.append(charge_power <= power_capacity)
        constraints.append(discharge_power <= power_capacity)

        # # Charge/discharge exclusivity
        # switch = cvx.Variable(steps_horizon_k, boolean=True, name="electric_storage_charge_discharge_switch")
        # constraints.append(charge_power[0, :] <= switch * power_capacity)
        # constraints.append(discharge_power[0, :] <= (1 - switch) * power_capacity)

        # Define balance equation
        # Position one in residual energy is equivalent to the position cero to the other variables
        constraints.append(
            residual_energy[0, 1 : steps_horizon_k + 1]
            == decay_factor * residual_energy[0, 0:steps_horizon_k]
            + (
                (
                    charging_efficiency * charge_power[0, 0:steps_horizon_k]
                    - discharge_power[0, 0:steps_horizon_k] / discharging_efficiency
                )
                * delta_time
            )
        )

        # Define optimization dispatch
        dispatch = charge_power - discharge_power

        return objective, constraints, dispatch

    def _process_data_as_arrays(
        self, electric_storage_info: Dict[str, Any], steps_horizon_k: int
    ) -> Dict[str, np.ndarray]:
        """Processes raw device data into NumPy arrays for the optimization model.

        This helper function takes the dictionary of data retrieved for the electric
        storage device and converts it into a structured dictionary of NumPy arrays.
        This format is required by the CVXPY optimization problem. It handles unit
        conversions (e.g., SoC from % to kWh) and validates the initial state
        against the defined SoC limits.

        Args:
            electric_storage_info: A dictionary containing the raw data and parameters
                                   for the electric storage device.
            steps_horizon_k: The number of time steps in the optimization horizon.

        Returns:
            A dictionary where keys are parameter names (e.g., 'initial_state',
            'power_capacity') and values are the corresponding NumPy arrays.
        """
        electric_storage_arrays = {}
        # Energy capacity of the battery
        energy_capacity = electric_storage_info["energy_capacity"]["battery"]
        electric_storage_arrays["energy_capacity"] = energy_capacity

        # Initial state of the battery
        initial_state = (
            electric_storage_info["initial_state"]["battery"]
            / 100
            * electric_storage_arrays["energy_capacity"]
        )
        electric_storage_arrays["initial_state"] = initial_state

        # Minimum and maximum residual energy of the battery
        min_residual_energy = (
            electric_storage_info["min_residual_energy"]["battery"]
            / 100
            * energy_capacity
        )
        max_residual_energy = (
            electric_storage_info["max_residual_energy"]["battery"]
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
            electric_storage_info["desired_state"]["battery"] / 100 * energy_capacity
        )

        # Priority of the battery
        electric_storage_arrays["priority"] = electric_storage_info["priority"][
            "battery"
        ]

        # Final state of charge requirement of the battery
        electric_storage_arrays["final_soc_requirement"] = (
            electric_storage_info["final_soc_requirement"]["battery"]
            / 100
            * electric_storage_arrays["energy_capacity"]
        )

        # Other variables
        electric_storage_arrays["power_capacity"] = electric_storage_info[
            "power_capacity"
        ]["battery"]
        electric_storage_arrays["decay_factor"] = electric_storage_info["decay_factor"][
            "battery"
        ]
        electric_storage_arrays["charging_efficiency"] = electric_storage_info[
            "charging_efficiency"
        ]["battery"]
        electric_storage_arrays["discharging_efficiency"] = electric_storage_info[
            "discharging_efficiency"
        ]["battery"]
        electric_storage_arrays["norm_factor"] = electric_storage_info[
            "energy_capacity"
        ]["battery"]

        return electric_storage_arrays
