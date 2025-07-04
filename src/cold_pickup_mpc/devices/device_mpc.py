from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Tuple

import cvxpy as cvx


class DeviceMPC(ABC):
    """Abstract base class for a device compatible with the Model Predictive Control (MPC).

    This class defines the interface that all controllable devices must implement
    to be included in the MPC optimization. It ensures that every device can
    provide its own set of objectives and constraints to the central optimization problem.
    """

    @abstractmethod
    def create_mpc_formulation(
        self,
        start: datetime,
        stop: datetime,
        steps_horizon_k: int,
        interval: int = 10,
        norm_factor: int = 10,
    ) -> Tuple[List, List, cvx.Variable]:
        """Creates the optimization formulation for the device.

        This method is responsible for defining the mathematical model of the device's
        behavior, including its operational constraints and its contribution to the
        overall optimization objective (e.g., minimizing energy cost, maximizing comfort).

        Args:
            start: The start time of the optimization horizon.
            stop: The end time of the optimization horizon.
            steps_horizon_k: The number of time steps in the optimization horizon.
            interval: The duration of each time step in minutes.
            norm_factor: A normalization factor used in the objective function to
                         balance different physical units and magnitudes.

        Returns:
            A tuple containing three elements:
            - A list of objective terms (cvxpy expressions) that the MPC will seek to minimize.
            - A list of constraints (cvxpy constraints) that model the device's physical
              and operational limitations.
            - A cvxpy.Variable representing the device's power dispatch over the horizon.
              This variable links the device's behavior to the building's total consumption.
        """
        return ([], [], cvx.Variable(steps_horizon_k))
