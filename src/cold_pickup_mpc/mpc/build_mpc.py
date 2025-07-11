"""This module defines the BuildGlobalMPC class, responsible for constructing and solving the overall MPC problem.

It integrates individual device-specific MPC formulations (from modules like
`electric_storage_mpc`, `space_heating_mpc`, etc.) into a single, comprehensive
optimization problem. This module handles the aggregation of objectives and
constraints from various controllable devices, incorporates global factors
like electricity prices and grid power limits, and manages the execution
of the CVXPY solver to determine optimal dispatch strategies.
"""

import os
from datetime import datetime
from time import time
from typing import Any, Dict, List, Tuple

import cvxpy as cvx
import numpy as np

from cold_pickup_mpc.devices.electric_storage_mpc import ElectricStorageMPC
from cold_pickup_mpc.devices.electric_vehicle_v1g_mpc import ElectricVehicleV1GMPC
from cold_pickup_mpc.devices.helper import DeviceHelper
from cold_pickup_mpc.devices.space_heating_mpc import SpaceHeatingMPC
from cold_pickup_mpc.devices.water_heater_mpc import WaterHeaterMPC
from cold_pickup_mpc.retrievers.api_calls import (
    get_devices,
    get_non_controllable_loads_forecast,
)
from cold_pickup_mpc.util.logging import LoggingUtil

logger = LoggingUtil.get_logger(__name__)


class BuildGlobalMPC:
    """Manages the construction and solution of the overall Model Predictive Control (MPC) problem.

    This class aggregates the individual MPC formulations from various controllable
    devices (e.g., electric storage, space heating, electric vehicles, water heaters)
    into a single, comprehensive optimization problem. It also incorporates global
    constraints such as electricity prices and grid power limits.
    """

    def __init__(
        self,
        space_heating: bool,
        electric_storage: bool,
        electric_vehicle: bool,
        water_heater: bool,
    ) -> None:
        """Initializes the BuildGlobalMPC with flags indicating which device types to include.

        Args:
            space_heating: A boolean indicating whether to include space heating devices.
            electric_storage: A boolean indicating whether to include electric storage devices.
            electric_vehicle: A boolean indicating whether to include electric vehicle devices.
            water_heater: A boolean indicating whether to include water heater devices.
        """
        # Instantiate devices
        self.devices = self._instantiate_devices(
            electric_storage, electric_vehicle, water_heater, space_heating
        )

    def solve_mpc(
        self,
        global_mpc_problem: cvx.Problem,
    ) -> cvx.Problem:
        """Solves the constructed global MPC problem.

        This method takes a CVXPY Problem object, solves it using the SCS solver,
        and logs the execution time and problem status.

        Args:
            global_mpc_problem: The CVXPY Problem object representing the aggregated MPC.

        Returns:
            The solved CVXPY Problem object, containing the optimal variable values.
        """
        start_time = time()
        verbose = os.getenv("VERBOSE_SOLVER_LOGS", "false").lower() == "true"
        global_mpc_problem.solve(solver=cvx.SCS, verbose=verbose)
        execution_time = time() - start_time
        logger.info("The solver took %.2f seconds to solve the problem", execution_time)
        logger.info("The status of the problem is: %s", global_mpc_problem.status)

        return global_mpc_problem

    def create_mpc_formulation(
        self,
        start: datetime,
        stop: datetime,
        interval: int,
        price_profile: Dict[datetime, float],
        power_limit: Dict[datetime, float],
    ) -> Tuple[cvx.Problem, cvx.Expression]:
        """Creates the full MPC formulation by aggregating all enabled devices.

        This method orchestrates the creation of the overall optimization problem.
        It retrieves forecasts for non-controllable loads, validates input data,
        and then iteratively calls the `create_mpc_formulation` method for each
        instantiated device to gather their objectives and constraints. Finally,
        it combines these with the global objective (minimizing energy cost) and
        constraints (e.g., grid power limits) to form the complete CVXPY problem.

        Args:
            start: The start time of the optimization horizon.
            stop: The end time of the optimization horizon.
            interval: The time step interval in minutes for the optimization horizon.
            price_profile: A dictionary mapping timestamps to electricity prices over the horizon.
            power_limit: A dictionary mapping timestamps to the maximum allowable grid power exchange.

        Returns:
            A tuple containing:
            - The constructed CVXPY Problem object.
            - A CVXPY Expression representing the net grid power exchange, which is
              the sum of all device dispatches and non-controllable loads.

        Raises:
            ValueError: If the stop time is not greater than the start time.
        """
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

        # Load the non controllable loads, power limit and price profile
        price_profile, power_limit_array, non_controllable_loads = (
            self._validate_global_inputs(
                start, stop, price_profile, power_limit, steps_horizon_k
            )
        )

        # Initialize devices (PV, ES, TS, EV) load objective, dispatch and constraints (only comfort terms)
        objectives_devices: List[Any] = []
        constraints_devices: List[Any] = []
        dispatch_devices: List[cvx.Variable] = []
        for device_name, device_mpc in self.devices.items():
            logger.info("Creating the MPC formulation for device %s", device_name)
            # Compute the time to build the MPC formulation
            start_time = time()
            obj, cons, disp = device_mpc.create_mpc_formulation(
                start, stop, steps_horizon_k, interval
            )
            execution_time = time() - start_time
            logger.info(
                "The creation of the MPC for device %s took %.2f seconds",
                device_name,
                execution_time,
            )
            objectives_devices.extend(obj)
            constraints_devices.extend(cons)
            dispatch_devices.append(disp)

        # Create a optimization parameter for the price
        price_parameter = cvx.Parameter(
            (1, price_profile.shape[1]), name="price", nonneg=True
        )
        price_parameter.value = price_profile

        # Compute the energy balance
        aggregated_dispatch = cvx.sum(dispatch_devices, axis=0)
        net_grid_power_exchange = aggregated_dispatch + non_controllable_loads

        # Define MPC objective
        global_mpc_objective = 0
        global_mpc_objective += cvx.sum(
            cvx.multiply(net_grid_power_exchange, price_parameter)
        ) + cvx.sum(objectives_devices, axis=0)

        # Define constraints
        global_mpc_constraints = []
        global_mpc_constraints.extend(
            constraints_devices
        )  # Add the constraints of the devices

        # Add constraint for the available power
        global_mpc_constraints.append(net_grid_power_exchange <= power_limit_array)

        # Build the optimization problem
        global_mpc_problem = cvx.Problem(
            cvx.Minimize(global_mpc_objective), global_mpc_constraints
        )
        logger.info("Global MPC problem is DCP: %s", global_mpc_problem.is_dcp())

        return global_mpc_problem, net_grid_power_exchange

    def _validate_global_inputs(
        self,
        start: datetime,
        stop: datetime,
        price_profile: Dict[datetime, float],
        power_limit: Dict[datetime, float],
        steps_horizon_k: int,
    ) -> Tuple[np.ndarray | None, np.ndarray | None, np.ndarray | None]:
        """Validates and processes global input data into NumPy arrays.

        This helper method retrieves non-controllable load forecasts and ensures
        that the time indices and lengths of the price profile, power limit, and
        non-controllable loads align with the optimization horizon. It converts
        these inputs into NumPy arrays suitable for CVXPY.

        Args:
            start: The start time of the optimization horizon.
            stop: The end time of the optimization horizon.
            price_profile: A dictionary mapping timestamps to electricity prices.
            power_limit: A dictionary mapping timestamps to power limits.
            steps_horizon_k: The number of time steps in the optimization horizon.

        Returns:
            A tuple containing three NumPy arrays (or None if validation fails):
            - `price_profile_array`: Array of electricity prices.
            - `power_limit_array`: Array of power limits.
            - `non_controllable_loads_array`: Array of non-controllable load forecasts.
        """
        # Define values by default
        price_profile_array = None
        power_limit_array = None
        non_controllable_loads_array = None

        # Retreive the non-controllable loads forecast
        non_controllable_loads = get_non_controllable_loads_forecast(
            "non-controllable-loads", start, stop
        )

        # Check if the inputs match the expected length
        if (
            len(price_profile)
            == len(power_limit)
            == len(non_controllable_loads["forecast"])
        ):
            price_start_date = list(price_profile.keys())[0]
            power_limit_start_date = list(power_limit.keys())[0]
            non_controllable_loads_start_date = datetime.fromisoformat(
                list(non_controllable_loads["forecast"].keys())[0]
            )

            if (
                price_start_date != power_limit_start_date
                or price_start_date != non_controllable_loads_start_date
            ):
                logger.error("Start dates of inputs do not match.")
            else:
                logger.debug("Start dates of inputs match.")
                non_controllable_loads_flat = np.array(
                    list(non_controllable_loads["forecast"].values())
                )[0:steps_horizon_k]
                non_controllable_loads_array = non_controllable_loads_flat.reshape(
                    (1, len(non_controllable_loads_flat))
                )

                # Compute price profile
                price_profile_flat = np.array(list(price_profile.values()))[
                    0:steps_horizon_k
                ]
                price_profile_array = price_profile_flat.reshape(
                    (1, len(price_profile_flat))
                )

                # Compute power limit
                power_limit_flat = np.array(list(power_limit.values()))[
                    0:steps_horizon_k
                ]
                power_limit_array = power_limit_flat.reshape((1, len(power_limit_flat)))

        return price_profile_array, power_limit_array, non_controllable_loads_array

    def _instantiate_devices(
        self,
        electric_storage: bool,
        electric_vehicle: bool,
        water_heater: bool,
        space_heating: bool,
    ) -> Dict[str, Any]:
        """Instantiates the MPC models for the selected controllable devices.

        This helper method queries the available devices from the Core API and,
        based on the provided boolean flags, creates instances of the corresponding
        DeviceMPC subclasses (e.g., ElectricStorageMPC, SpaceHeatingMPC).
        It logs which devices are being instantiated or skipped.

        Args:
            electric_storage: If True, attempts to instantiate ElectricStorageMPC.
            electric_vehicle: If True, attempts to instantiate ElectricVehicleV1GMPC.
            water_heater: If True, attempts to instantiate WaterHeaterMPC.
            space_heating: If True, attempts to instantiate SpaceHeatingMPC.

        Returns:
            A dictionary where keys are device types (strings) and values are
            the instantiated DeviceMPC objects.
        """
        devices_mcp: Dict[str, Any] = {}

        all_devices = get_devices()["content"]

        # Create the electric storage
        if electric_storage:
            device_type = DeviceHelper.ELECTRIC_STORAGE.value
            devices = DeviceHelper.get_all_device_info_by_key(
                all_devices, "type", device_type
            )
            if devices:
                devices_mcp[device_type] = ElectricStorageMPC(devices)
            else:
                logger.info(
                    "No electric storage devices found. Skipping electric storage device MPC creation."
                )

        # Create the electric vehicle
        if electric_vehicle:
            device_type = DeviceHelper.ELECTRIC_VEHICLE_V1G.value
            devices = DeviceHelper.get_all_device_info_by_key(
                all_devices, "type", device_type
            )
            if devices:
                devices_mcp[device_type] = ElectricVehicleV1GMPC(devices)
            else:
                logger.info(
                    "No electric vehicle devices found. Skipping electric vehicle device MPC creation."
                )

        # Create the water heater
        if water_heater:
            device_type = DeviceHelper.WATER_HEATER.value
            devices = DeviceHelper.get_all_device_info_by_key(
                all_devices, "type", device_type
            )
            if devices:
                devices_mcp[device_type] = WaterHeaterMPC(devices)
            else:
                logger.info(
                    "No water heater devices found. Skipping water heater device MPC creation."
                )

        # Create the smart thermsotat
        if space_heating:
            device_type = DeviceHelper.SPACE_HEATING.value
            devices = DeviceHelper.get_all_device_info_by_key(
                all_devices, "type", device_type
            )
            if devices:
                devices_mcp[device_type] = SpaceHeatingMPC(devices)
            else:
                logger.info(
                    "No space heating devices found. Skipping space heating device MPC creation."
                )

        return devices_mcp
