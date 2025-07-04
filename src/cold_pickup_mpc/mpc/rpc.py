"""This module handles the Remote Procedure Call (RPC) communication for the MPC system.

It sets up a Redis-based message broker using FastStream to listen for incoming
MPC requests. The `handle_mpc_request` asynchronous function processes these
requests, extracts relevant parameters, and then schedules the main MPC
optimization and real-time control jobs. This module acts as the entry point
for external systems to trigger MPC runs.
"""

from datetime import datetime
from typing import Any, Dict

from faststream.redis import RedisRouter

from cold_pickup_mpc.util.logging import LoggingUtil

logger = LoggingUtil.get_logger(__name__)
logger.info("The MPC subscriber is starting at %s:", str(datetime.now().astimezone()))


# TODO read from ENV file
topic_prefix = "grid_function/"
function_name = "mpc"


mpc_router = RedisRouter(prefix=topic_prefix)


@mpc_router.subscriber(function_name)
async def handle_mpc_request(mpc_request: Dict[str, Any]) -> bool:
    """Handles incoming MPC requests via Redis RPC.

    This asynchronous function acts as a subscriber to the 'mpc' topic.
    It receives MPC parameters, validates them, and then schedules the
    main MPC and control jobs. If no parameters are provided, it
    interprets this as a signal to stop the real-time control job.

    Args:
        mpc_request: A dictionary containing the MPC request, expected to have
                     a 'params' key with detailed optimization parameters.

    Returns:
        True if the MPC and control jobs are successfully scheduled, False otherwise.
    """
    params = mpc_request.get("params")
    if params is None:
        logger.info(
            "Received MPC request with NO parameters, stopping the Real-Time Control job"
        )
        from cold_pickup_mpc.app import stop_realtime_control_job

        stop_realtime_control_job()
        return False

    logger.info("Received MPC request with parameters: %s", params)

    space_heating = params["space_heating"]
    electric_storage = params["electric_storage"]
    electric_vehicle = params["electric_vehicle"]
    water_heater = params["water_heater"]
    start = datetime.fromisoformat(params["start"])
    stop = datetime.fromisoformat(params["stop"])
    interval = int(params["interval"])
    prices = {datetime.fromisoformat(k): v for k, v in params["prices"].items()}
    power_limit = {
        datetime.fromisoformat(k): v for k, v in params["power_limit"].items()
    }

    from cold_pickup_mpc.app import schedule_mpc_and_control_jobs

    schedule_mpc_and_control_jobs(
        space_heating,
        electric_storage,
        electric_vehicle,
        water_heater,
        power_limit,
        start,
        stop,
        interval,
        prices,
    )

    return True
