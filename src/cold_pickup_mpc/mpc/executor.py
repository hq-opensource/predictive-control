from datetime import datetime
from typing import Dict, Tuple

import cvxpy as cvx

from cold_pickup_mpc.mpc.build_mpc import BuildGlobalMPC
from cold_pickup_mpc.util.logging import LoggingUtil


logger = LoggingUtil.get_logger(__name__)


class ExecutorMPC:
    """Class to build the full MPC formulation from individual devices."""

    def __init__(
        self,
        space_heating: bool,
        electric_storage: bool,
        electric_vehicle: bool,
        water_heater: bool,
    ) -> None:
        """Initialize with configuration containing device info and global parameters."""
        self._space_heating = space_heating
        self._electric_storage = electric_storage
        self._electric_vehicle = electric_vehicle
        self._water_heater = water_heater

        # Create the BuildGlobalMPC object
        self._build_mpc = BuildGlobalMPC(space_heating, electric_storage, electric_vehicle, water_heater)

    def run_mpc(
        self,
        start: datetime,
        stop: datetime,
        interval: int,
        price_profile: Dict[datetime, float],
        power_limit: Dict[datetime, float],
    ) -> Tuple[cvx.Problem, cvx.Expression]:
        # Build the MPC
        global_mpc_problem, net_grid_power_exchange = self._build_mpc.create_mpc_formulation(
            start, stop, interval, price_profile, power_limit
        )

        # Solve the MPC
        global_mpc_problem = self._build_mpc.solve_mpc(global_mpc_problem)

        return global_mpc_problem, net_grid_power_exchange
