import time

from typing import Any, Dict, List

import cvxpy as cp
import numpy as np

from cvxpy import settings as cp_settings

from cold_pickup_mpc.util.logging import LoggingUtil


logger = LoggingUtil.get_logger(__name__)


class ThermalModels:
    """Provides the optimization models used to execute the learning of the thermal models."""

    def __init__(self) -> None:
        """Currently this class do not take any inputs."""
        pass

    def learn_black_model(
        self,
        x_internal_states: np.ndarray,
        u_heaters: np.ndarray,
        w_external_variables: np.ndarray,
        learning_weigths: List = [1, 1, 1],
        verbose: bool = False,
    ) -> Dict[str, Any] | None:
        """
            Method created to learn the thermal dynamics of residential houses.

        1.  Objective:

            ..  math::
                J = ||estimated_Y - Y||_2^2 + lx ||Ax||_2 + lu * ||Au||_2 + lw ||Aw||_2
                :label: eq_learning_obj_1

            Where estimated_Y:

            ..  math::
                estimated_Y = AxX + AuU + AwW
                :label: eq_learning_obj_2

            And Y is the measured temperature in each room of the home.

        2.  Constraints:
            Diagonal matrix:
            ..  math::
                diag(Au) >= 0.02
                :label: eq_learning_cons_1

            Stability:
            ..  math::
                0 <= Ax <= 0.98
                :label: eq_learning_cons_2

                ..  math::
                Aw >= 0
                :label: eq_learning_cons_2

        3.  Optimization variables:

            :math:`Ax`, :math:`Au`, and :math:`Aw`.

        4. Variable names

            :math:`Ax` = Weights for the internal states (temperature measurements).

            :math:`Au` = Weights for the control variables (power consumption measurements in the heaters).

            :math:`Aw` = Weights for the external variables (temperature, solar radiation, etc).

        """
        # Build numpy arrays
        Y = x_internal_states.iloc[1:].T.to_numpy().astype(float)  # All values except the first one
        X = x_internal_states.iloc[:-1].T.to_numpy().astype(float)  # All values except the last one
        U = u_heaters.iloc[:-1].T.to_numpy().astype(float)  # All values except the last one
        W = w_external_variables.iloc[:-1].T.to_numpy().astype(float)  # All values except the last one

        self.Umax = u_heaters.max().tolist()

        n = X.shape[0]
        m = U.shape[0]
        l_dim = W.shape[0]

        Ax = cp.Variable((n, n), nonneg=True, name="learning_x_temperature")
        Aw = cp.Variable((n, l_dim), nonneg=True, name="learning_w_external_variables")
        diagonal_matrix = np.zeros((n, m))
        np.fill_diagonal(diagonal_matrix, 1)
        Au = cp.multiply(cp.Variable((n, m), nonneg=True, name="learning_u_heaters"), diagonal_matrix)

        constraints = []
        constraints = [cp.diag(Au) >= 0.0015]
        constraints += [Ax <= 0.9995]
        # Validate dimensions
        logger.info("Validating matrix multiplication for the optimimzation problem.")
        logger.info("Ax second dimension: %s || X first dimension: %s", Ax.shape[1], X.shape[0])
        logger.info("Au second dimension: %s || U first dimension: %s", Au.shape[1], U.shape[0])
        logger.info("Aw second dimension: %s || W first dimension: %s", Aw.shape[1], W.shape[0])
        logger.info("Validating historical data for the optimimzation problem:")
        logger.info("X historic len: %s", X.shape[1])
        logger.info("U historic len: %s", U.shape[1])
        logger.info("W historic len: %s", W.shape[1])

        # Execute the optimization problem only if the dimensions match!
        results = None  # Overwrite only if problem optimization is succesful!
        if X.shape[1] == U.shape[1] and X.shape[1] == W.shape[1]:
            if Ax.shape[1] == X.shape[0] and Au.shape[1] == U.shape[0] and Aw.shape[1] == W.shape[0]:
                estimated_Y = cp.matmul(Ax, X) + cp.matmul(Au, U) + cp.matmul(Aw, W)

                lx, lu, lw = learning_weigths[0], learning_weigths[1], learning_weigths[2]
                optimization_objective = cp.Minimize(
                    cp.sum_squares(estimated_Y - Y)
                    + lx * cp.pnorm(Ax, p=2)
                    + lu * cp.pnorm(Au, p=2)
                    + lw * cp.pnorm(Aw, p=2)
                )

                problem = cp.Problem(optimization_objective, constraints=constraints)

                start_time = time.time()
                problem.solve(solver=cp.SCS, verbose=verbose)
                end_time = time.time()

                execution_time = end_time - start_time
                logger.info("Learning the thermal model took %.2f seconds", round(execution_time, 2))

                # Verify if the optimization problem was solved
                if problem.status in cp_settings.SOLUTION_PRESENT:
                    logger.debug("I have learned the thermal dynamic of the house!")
                    results = {
                        "Ax": Ax.value.tolist(),
                        "Au": Au.value.tolist(),
                        "Aw": Aw.value.tolist(),
                    }
                else:
                    logger.warning("Optimization problem executed but learning failed! Returning none!")
            else:
                logger.warning("Optimization problem was not solved!")
                logger.warning("Dimensions of historic or arrays do not match!")
                logger.warning("Returning none!")
        else:
            logger.warning("Optimization problem was not solved!")
            logger.warning("Dimensions of historic or arrays do not match!")
            logger.warning("Returning none!")

        return results
