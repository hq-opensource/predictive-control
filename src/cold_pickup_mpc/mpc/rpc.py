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
    params = mpc_request.get("params")
    if params is None:
        logger.info("Received MPC request with NO parameters, stopping the Real-Time Control job")
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
    power_limit = {datetime.fromisoformat(k): v for k, v in params["power_limit"].items()}

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
