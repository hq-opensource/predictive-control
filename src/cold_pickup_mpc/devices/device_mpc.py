from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Tuple

import cvxpy as cvx


class DeviceMPC(ABC):
    """Abstract class for a device that can be used for an MPC."""

    @abstractmethod
    def create_mpc_formulation(
        self, start: datetime, stop: datetime, steps_horizon_k: int, interval: int = 10, norm_factor: int = 10
    ) -> Tuple[List, List, cvx.Variable]:
        """Creates the optimization formulation of each device.

        Args:
            start: Start time of the optimization horizon.
            stop: End time of the optimization horizon.
            interval: Time step interval in minutes.
            initial_state: Initial state of the device as a DataFrame.
            **kwargs: Additional device-specific arguments.

        Returns:
            Tuple containing:
            - List of objective terms.
            - List of constraints.
            - CVXPY variable representing the dispatch.
        """
        return ([], [], [])
