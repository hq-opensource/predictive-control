"""This module defines the ExecutorMPC class, which orchestrates the Model Predictive Control (MPC) process.

It serves as the primary interface for initiating and running an MPC optimization cycle.
The ExecutorMPC is responsible for:
- Initializing the global MPC problem builder (`BuildGlobalMPC`).
- Constructing the comprehensive optimization problem based on selected device types.
- Solving the formulated MPC problem to determine optimal control actions.
- Returning the solved problem and the resulting net grid power exchange.
"""

from datetime import datetime
from typing import Dict, Tuple

import cvxpy as cvx

from cold_pickup_mpc.mpc.build_mpc import BuildGlobalMPC
from cold_pickup_mpc.util.logging import LoggingUtil

logger = LoggingUtil.get_logger(__name__)


class ExecutorMPC:
    """Orchestrates the execution of the Model Predictive Control (MPC) process.

    This class is responsible for initializing the global MPC problem builder,
    constructing the optimization problem based on specified device types,
    solving the problem, and returning the results. It acts as the main entry
    point for running an MPC optimization cycle.
    """

    def __init__(
        self,
        space_heating: bool,
        electric_storage: bool,
        electric_vehicle: bool,
        water_heater: bool,
    ) -> None:
        """Initializes the ExecutorMPC with flags indicating which device types to include.

        Args:
            space_heating: A boolean indicating whether to include space heating devices.
            electric_storage: A boolean indicating whether to include electric storage devices.
            electric_vehicle: A boolean indicating whether to include electric vehicle devices.
            water_heater: A boolean indicating whether to include water heater devices.
        """
        self._space_heating = space_heating
        self._electric_storage = electric_storage
        self._electric_vehicle = electric_vehicle
        self._water_heater = water_heater

        # Create the BuildGlobalMPC object
        self._build_mpc = BuildGlobalMPC(
            space_heating, electric_storage, electric_vehicle, water_heater
        )

    def run_mpc(
        self,
        start: datetime,
        stop: datetime,
        interval: int,
        price_profile: Dict[datetime, float],
        power_limit: Dict[datetime, float],
    ) -> Tuple[cvx.Problem, cvx.Expression]:
        """Executes a full MPC optimization cycle.

        This method first calls the `create_mpc_formulation` method of the
        `BuildGlobalMPC` instance to construct the optimization problem.
        Then, it calls the `solve_mpc` method to find the optimal solution.

        Args:
            start: The start time of the optimization horizon.
            stop: The end time of the optimization horizon.
            interval: The time step interval in minutes for the optimization horizon.
            price_profile: A dictionary mapping timestamps to electricity prices over the horizon.
            power_limit: A dictionary mapping timestamps to the maximum allowable grid power exchange.

        Returns:
            A tuple containing:
            - The solved CVXPY Problem object.
            - A CVXPY Expression representing the net grid power exchange, which is
              the sum of all device dispatches and non-controllable loads.
        """
        # Build the MPC
        global_mpc_problem, net_grid_power_exchange = (
            self._build_mpc.create_mpc_formulation(
                start, stop, interval, price_profile, power_limit
            )
        )

        # Solve the MPC
        global_mpc_problem = self._build_mpc.solve_mpc(global_mpc_problem)

        return global_mpc_problem, net_grid_power_exchange
