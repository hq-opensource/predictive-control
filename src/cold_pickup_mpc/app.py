import asyncio
import os

from datetime import datetime, timedelta
from typing import Any, Dict

from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED, JobEvent
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from faststream import FastStream
from faststream.redis import RedisBroker

from cold_pickup_mpc.mpc.executor import ExecutorMPC
from cold_pickup_mpc.mpc.interpreter import Interpreter
from cold_pickup_mpc.mpc.rpc import mpc_router
from cold_pickup_mpc.mpc.schedule import post_controls_schedule
from cold_pickup_mpc.real_time.power_limit_mpc import RealTimeControl
from cold_pickup_mpc.util.logging import LoggingUtil


logger = LoggingUtil.get_logger(__name__)
scheduler = BackgroundScheduler()
scheduler.start()
job_controls: Dict[str, Any] = {}


def job_finished_listener(event: JobEvent) -> None:
    """Listener that will be called when a job is completed or has failed"""
    job_id = event.job_id
    if job_id in job_controls:
        logger.info(f"Control job {job_id} completed, cleaning up resources")
        del job_controls[job_id]


# Add the listener for job completion events
scheduler.add_listener(job_finished_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)


def _mpc_job(
    space_heating: bool,
    electric_storage: bool,
    electric_vehicle: bool,
    water_heater: bool,
    start: datetime,
    stop: datetime,
    interval: int,
    prices: Dict[datetime, float],
    power_limit: Dict[datetime, float],
) -> None:
    logger.info("Running MPC job")
    executor = ExecutorMPC(space_heating, electric_storage, electric_vehicle, water_heater)

    global_mpc_problem, net_grid_power_exchange = executor.run_mpc(start, stop, interval, prices, power_limit)

    logger.info("MPC completed successfully")

    interpreter = Interpreter(start, stop)
    controls = interpreter.interpret(
        global_mpc_problem, space_heating, electric_storage, electric_vehicle, water_heater
    )
    post_controls_schedule(controls)


def schedule_mpc_and_control_jobs(
    space_heating: bool,
    electric_storage: bool,
    electric_vehicle: bool,
    water_heater: bool,
    power_limit: Dict[datetime, float],
    start: datetime,
    stop: datetime,
    interval: int,
    prices: Dict[datetime, float],
) -> None:
    # We try to start the MPC 10 minutes before the start time, or now if it's in the past
    start_mpc = max(start - timedelta(minutes=10), datetime.now().astimezone())
    mpc_trigger = DateTrigger(run_date=start_mpc)
    logger.info("Adding MPC job to scheduler for date: %s", start_mpc)
    scheduler.add_job(
        _mpc_job,
        trigger=mpc_trigger,
        args=[
            space_heating,
            electric_storage,
            electric_vehicle,
            water_heater,
            start,
            stop,
            interval,
            prices,
            power_limit,
        ],
    )

    # We schedule the real-time control job
    control = RealTimeControl(power_limit, space_heating, electric_storage, electric_vehicle, water_heater)
    control_trigger = DateTrigger(run_date=start)
    logger.info("Adding Real-Time Control job to scheduler for date: %s", start)
    job = scheduler.add_job(control.run, trigger=control_trigger)

    # Store a reference to the control object in the job_controls dictionary
    job_controls[job.id] = control


def stop_realtime_control_job() -> None:
    logger.info("Stopping Real-Time Control job")
    for job in scheduler.get_jobs():
        job_id = job.id
        if job_id in job_controls and job_controls[job_id].is_running:
            job_controls[job_id].must_run = False
            logger.info("Real-Time Control job stopped")
            break
    else:
        logger.info("No Real-Time Control job found to stop")


def main() -> None:
    # Redis event broker setup
    redis_password = os.getenv("REDIS_PASSWORD")
    redis_host = os.getenv("REDIS_HOST")
    redis_port = os.getenv("REDIS_PORT")
    redis_url = f"redis://:{redis_password}@{redis_host}:{redis_port}"
    broker = RedisBroker(redis_url)

    # Include routers on the broker
    broker.include_router(mpc_router)

    # Create the app
    broker_events_app = FastStream(broker)

    # Start the subscription to the forecasters
    asyncio.run(broker_events_app.run())


def test_executor_mpc() -> None:
    # Define devices to use
    space_heating = False
    electric_storage = False
    electric_vehicle = False
    water_heater = True

    # Create object
    executor_mpc = ExecutorMPC(space_heating, electric_storage, electric_vehicle, water_heater)

    # Time settings
    start_optimization = datetime.fromisoformat("2025-05-26T19:00:00-04:00")
    stop_optimization = start_optimization + timedelta(hours=2)
    interval = 10  # in minutes

    # Generate timestamps
    timestamps = [start_optimization + timedelta(minutes=i) for i in range(0, 120 + 1, interval)]

    # Example: Generate dummy values
    price_profile = {ts: 0.07 if ts.minute < 40 else 0.15 for ts in timestamps}
    power_limit = {ts: 7.0 if ts.minute < 40 else 15.0 for ts in timestamps}

    # Execute the MPC
    global_mpc_problem, net_grid_power_exchange = executor_mpc.run_mpc(
        start_optimization, stop_optimization, interval, price_profile, power_limit
    )

    # Create the interpreter to read results
    interpreter = Interpreter(start_optimization, stop_optimization)
    controls = interpreter.interpret(
        global_mpc_problem, space_heating, electric_storage, electric_vehicle, water_heater
    )
    post_controls_schedule(controls)
    logger.info("MPC job completed successfully, controls posted to the schedule.")


def test_real_time_control(start_control: datetime) -> None:
    """Test the real-time control job"""
    # Time settings

    interval = 10  # in minutes

    # Generate timestamps
    timestamps = [start_control + timedelta(minutes=i) for i in range(0, 120 + 1, interval)]
    # Test the real-time control job
    power_limit = {ts: 7.0 if ts.minute < 40 else 15.0 for ts in timestamps}

    real_time_control = RealTimeControl(power_limit)
    real_time_control.run()


if __name__ == "__main__":
    main()
    # Uncomment the following line to run the test function
    # test_executor_mpc()
    # start_control = datetime.fromisoformat("2025-05-20T14:41:00-04:00")
    # test_real_time_control(start_control)
