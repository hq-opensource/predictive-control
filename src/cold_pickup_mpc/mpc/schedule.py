from typing import Dict

import pandas as pd

from cold_pickup_mpc.devices.api_calls import write_schedule


def post_controls_schedule(controls: pd.DataFrame) -> None:
    controls_dict = _convert_dataframe_to_dict(controls)
    write_schedule(controls_dict)


def _convert_dataframe_to_dict(schedule: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    result_dict = {}

    # For each device/room, create a sub-dictionary with timestamps and dispatches
    for device_id in schedule.columns:
        device_dispach = {}

        for timestamp, value in schedule[device_id].items():
            iso_timestamp = timestamp.isoformat()
            device_dispach[iso_timestamp] = value

        result_dict[device_id] = device_dispach

    return result_dict
