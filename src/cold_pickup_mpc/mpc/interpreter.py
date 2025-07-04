"""This module defines the Interpreter class, responsible for processing and persisting MPC optimization results.

It extracts optimal variable values from the solved CVXPY problem, transforms them
into structured data (e.g., Pandas DataFrames), and handles their storage in a
time-series database like InfluxDB. The Interpreter ensures that the complex
outputs of the MPC solver are converted into actionable and storable insights,
providing a clear view of the system's optimized behavior and control signals.
"""

"""Module providing a class to interpret the results of the CVXPY Model Predictive Control optimization problem."""

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
import yaml
from cvxpy import Problem
from influxdb_client import InfluxDBClient, WriteApi
from influxdb_client.client.write_api import SYNCHRONOUS

from cold_pickup_mpc.devices.helper import DeviceHelper
from cold_pickup_mpc.util.logging import LoggingUtil

logger = LoggingUtil.get_logger(__name__)


class Interpreter:
    """Interprets and processes the results of the CVXPY Model Predictive Control (MPC) optimization problem.

    This class is responsible for extracting optimal variable values from the solved
    CVXPY problem, transforming them into meaningful data structures (e.g., Pandas DataFrames),
    and persisting these results to a time-series database like InfluxDB. It handles
    device-specific result interpretation and data formatting.
    """

    def __init__(self, start: datetime, stop: datetime) -> None:
        """Initializes the Interpreter with the start and stop times of the optimization horizon.

        Args:
            start: The start datetime of the optimization horizon.
            stop: The end datetime of the optimization horizon.
        """
        self.start: datetime = start
        self.stop: datetime = stop

    def interpret(
        self,
        global_mpc_problem: Problem,
        space_heating: bool,
        electric_storage: bool,
        electric_vehicle: bool,
        water_heater: bool,
    ) -> pd.DataFrame:
        """Interprets the results of the global MPC problem and saves them.

        This is the main method for processing the optimization output. It iterates
        through the enabled device types, extracts their respective control and
        state variables from the solved `global_mpc_problem`, converts them into
        Pandas DataFrames, and then saves these results to InfluxDB. It also
        aggregates the control signals into a single DataFrame.

        Args:
            global_mpc_problem: The solved CVXPY Problem object.
            space_heating: A boolean indicating if space heating devices were included.
            electric_storage: A boolean indicating if electric storage devices were included.
            electric_vehicle: A boolean indicating if electric vehicle devices were included.
            water_heater: A boolean indicating if water heater devices were included.

        Returns:
            A Pandas DataFrame containing the aggregated control signals for all
            controllable devices over the optimization horizon.
        """
        # Load and sort devices
        devices = DeviceHelper.sort_devices_by_priorities(
            space_heating, electric_storage, electric_vehicle, water_heater
        )

        date_range = pd.date_range(
            start=self.start,
            end=self.stop,
            freq="10min",
        )[:-1]

        # Initialize DataFrame for controls
        controls = pd.DataFrame(index=date_range)

        url = os.getenv("INFLUXDB_URL")
        org = os.getenv("INFLUXDB_ORG")
        token = os.getenv("INFLUXDB_TOKEN")
        influxdb_client = InfluxDBClient(url=url, token=token, org=org, timeout=30000)
        write_api = influxdb_client.write_api(write_options=SYNCHRONOUS)

        current_dir = Path(__file__).parent
        mapping_path = current_dir.parent / "database" / "influx_mapping.yaml"

        with open(mapping_path, "r") as file:
            influxdb_mapping = yaml.safe_load(file)

        if space_heating:
            results_space_heating, control_space_heating = (
                self.load_space_heating_variables(global_mpc_problem, devices)
            )
            # Create control
            controls = pd.concat([controls, control_space_heating], axis=1)

            # Save results to InfluxDB
            measurement = influxdb_mapping["sh_power"]["measurement"]
            data = self._convert_results_to_list(results_space_heating, measurement)
            bucket = influxdb_mapping["sh_power"]["bucket"]
            self._save_results_to_influxdb(
                data, bucket, DeviceHelper.SPACE_HEATING.value, write_api
            )
        if electric_storage:
            results_electric_storage, control_electric_storage = (
                self.load_electric_storage_variables(global_mpc_problem, devices)
            )
            # Create control
            controls = pd.concat([controls, control_electric_storage], axis=1)

            # Save results to InfluxDB
            measurement = influxdb_mapping["eb_net_power"]["measurement"]
            data = self._convert_results_to_list(results_electric_storage, measurement)
            bucket = influxdb_mapping["eb_net_power"]["bucket"]
            self._save_results_to_influxdb(
                data, bucket, DeviceHelper.ELECTRIC_STORAGE.value, write_api
            )
        if water_heater:
            results_water_heater, control_water_heater = (
                self.load_water_heater_variables(global_mpc_problem, devices)
            )
            # Create control
            controls = pd.concat([controls, control_water_heater], axis=1)

            # Save results to InfluxDB
            measurement = influxdb_mapping["wh_power"]["measurement"]
            data = self._convert_results_to_list(results_water_heater, measurement)
            bucket = influxdb_mapping["wh_power"]["bucket"]
            self._save_results_to_influxdb(
                data, bucket, DeviceHelper.WATER_HEATER.value, write_api
            )

        return controls

    def _convert_results_to_list(self, results: pd.DataFrame, measurement: str) -> List:
        """Converts a Pandas DataFrame of optimization results into a list of dictionaries.

        This format is suitable for writing data to InfluxDB. Each row in the DataFrame
        is converted into one or more dictionary entries, with timestamps, measurements,
        tags, and field values.

        Args:
            results: A Pandas DataFrame containing the optimization results.
            measurement: The InfluxDB measurement name to associate with the data.

        Returns:
            A list of dictionaries, each representing a data point for InfluxDB.
        """
        data = []
        for timestamp, row in results.iterrows():
            for column, value in row.items():
                if pd.notna(value):
                    data.append(
                        {
                            "measurement": measurement,
                            "tags": {"_type": "mpc_results"},
                            "time": timestamp,
                            "fields": {column: value},
                        }
                    )
        return data

    def _save_results_to_influxdb(
        self, data: List, bucket: str, device_type: str, write_api: WriteApi
    ) -> None:
        """Saves a list of data points to InfluxDB.

        This helper method handles the actual writing of data to the specified
        InfluxDB bucket using the provided WriteApi client. It includes logging
        for success and error handling.

        Args:
            data: A list of dictionaries, formatted for InfluxDB.
            bucket: The InfluxDB bucket to write the data to.
            device_type: A string indicating the type of device the results belong to (for logging).
            write_api: An initialized InfluxDB WriteApi client.
        """
        if not data:
            logger.warning("No data to write to InfluxDB.")
            return
        try:
            write_api.write(bucket=bucket, record=data)
            logger.info(
                "Results for the %s successfully saved to InfluxDB.", device_type
            )
        except Exception as e:
            logger.error("Failed to save results to InfluxDB: %s", str(e))

    def load_water_heater_variables(
        self,
        global_mpc_problem: Problem,
        devices: List[Dict[str, Any]],
        interval: int = 10,
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Extracts and processes water heater variables from the solved MPC problem.

        This method retrieves the optimal power dispatch and temperature profiles
        for the water heater from the `global_mpc_problem`'s variables. It then
        formats these into Pandas DataFrames for further use and storage.

        Args:
            global_mpc_problem: The solved CVXPY Problem object.
            devices: A list of device dictionaries, used to retrieve entity IDs.
            interval: The time step interval in minutes.

        Returns:
            A tuple containing two Pandas DataFrames:
            - `results_water_heater`: Contains the raw power and temperature profiles.
            - `control_water_heater`: Contains the control signals (power) mapped to device entity IDs.
        """

        # Build columns for the dataframes
        wh_power = ["wh_power"]  # 0-100%
        wh_temperature = ["wh_temperature"]  # kWh

        # Build index
        date_range = pd.date_range(
            start=self.start,
            end=self.stop,
            freq=f"{interval}min",
        )[:-1]  # Remove the last timestamp
        # Initialize DataFrames
        wh_power_df = pd.DataFrame(columns=wh_power, index=date_range)
        wh_temperature_df = pd.DataFrame(columns=wh_temperature, index=date_range)

        # Extract variable names and values from the global_mpc_problem
        for variable in global_mpc_problem.variables():
            # Assuming var has a name and a value method
            if variable.name() == "water_heater_power":
                var_array = np.around(variable.value.T, 3)
                wh_power_df = pd.DataFrame(
                    data=var_array, columns=wh_power, index=date_range
                )
            elif variable.name() == "water_heater_temperature":
                var_array = np.around(variable.value.T, 3)[1:]
                wh_temperature_df = pd.DataFrame(
                    data=var_array, columns=wh_temperature, index=date_range
                )

        # Create the final DataFrames
        column_entity_id = DeviceHelper.get_all_values_by_filtering_devices(
            device_list=devices,
            filter_key="type",
            filter_value="water_heater",
            target_key="entity_id",
        )
        results_water_heater = pd.concat([wh_power_df, wh_temperature_df], axis=1)
        control_water_heater = pd.DataFrame(
            data=results_water_heater[wh_power].values,
            columns=column_entity_id,
            index=date_range,
        )
        return results_water_heater, control_water_heater

    def load_electric_storage_variables(
        self,
        global_mpc_problem: Problem,
        devices: List[Dict[str, Any]],
        interval: int = 10,
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Extracts and processes electric storage variables from the solved MPC problem.

        This method retrieves the optimal charge/discharge power, residual energy,
        and state of charge (SoC) for the electric storage device from the
        `global_mpc_problem`'s variables. It then formats these into Pandas DataFrames.

        Args:
            global_mpc_problem: The solved CVXPY Problem object.
            devices: A list of device dictionaries, used to retrieve device parameters.
            interval: The time step interval in minutes.

        Returns:
            A tuple containing two Pandas DataFrames:
            - `results_electric_storage`: Contains the raw charge/discharge power,
                                          residual energy, net power, and SoC profiles.
            - `control_electric_storage`: Contains the net power control signals
                                          mapped to device entity IDs.
        """

        # Build columns for the dataframes
        state_of_charge = ["state_of_charge"]  # 0-100%
        residual_energy = ["residual_energy"]  # kWh
        battery_power = ["battery_power"]  # Net power in kW
        charge_power = ["charge_power"]  # Charge power in kW
        discharge_power = ["discharge_power"]  # Discharge power in kW

        # Build index
        date_range = pd.date_range(
            start=self.start,
            end=self.stop,
            freq=f"{interval}min",
        )[:-1]  # Remove the last timestamp
        # Initialize DataFrames
        soc_charge_df = pd.DataFrame(columns=state_of_charge, index=date_range)
        residual_energy_df = pd.DataFrame(columns=residual_energy, index=date_range)
        net_power_df = pd.DataFrame(columns=battery_power, index=date_range)
        charge_df = pd.DataFrame(columns=charge_power, index=date_range)
        discharge_df = pd.DataFrame(columns=discharge_power, index=date_range)

        # Extract variable names and values from the global_mpc_problem
        for variable in global_mpc_problem.variables():
            # Assuming var has a name and a value method
            if variable.name() == "electric_storage_charge_power":
                var_array = np.around(variable.value.T, 3)
                charge_df = pd.DataFrame(
                    data=var_array, columns=charge_power, index=date_range
                )
            elif variable.name() == "electric_storage_discharge_power":
                var_array = np.around(variable.value.T, 3)
                discharge_df = pd.DataFrame(
                    data=var_array, columns=discharge_power, index=date_range
                )
            elif variable.name() == "electric_storage_residual_energy":
                var_array = np.around(variable.value.T, 3).flatten()[
                    1:
                ]  # Skip the first timestamp (sync state)
                residual_energy_df = pd.DataFrame(
                    data=var_array, columns=residual_energy, index=date_range
                )

        # Compute the total net power
        net_power = charge_df["charge_power"] - discharge_df["discharge_power"]
        net_power_df = pd.DataFrame(
            data=net_power, columns=battery_power, index=date_range
        )

        # Compute the state of charge
        energy_capacity = DeviceHelper.get_all_values_by_filtering_devices(
            device_list=devices,
            filter_key="type",
            filter_value="electric_storage",
            target_key="energy_capacity",
        )  # Assumes that there is only one electric storage
        soc_charge = np.around(
            (residual_energy_df["residual_energy"] / energy_capacity * 100).values, 3
        )  # Assuming 10 kWh is the total capacity
        soc_charge_df = pd.DataFrame(
            data=soc_charge, columns=state_of_charge, index=date_range
        )

        # Create the final DataFrame
        results_electric_storage = pd.concat(
            [charge_df, discharge_df, residual_energy_df, net_power_df, soc_charge_df],
            axis=1,
        )

        # Create the final DataFrames
        column_entity_id = DeviceHelper.get_all_values_by_filtering_devices(
            device_list=devices,
            filter_key="type",
            filter_value="electric_storage",
            target_key="entity_id",
        )
        control_electric_storage = pd.DataFrame(
            data=results_electric_storage[battery_power].values,
            columns=column_entity_id,
            index=date_range,
        )

        return results_electric_storage, control_electric_storage

    def load_space_heating_variables(
        self,
        global_mpc_problem: Problem,
        devices: List[Dict[str, Any]],
        interval: int = 10,
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Extracts and processes space heating variables from the solved MPC problem.

        This method retrieves the optimal heater power dispatch and indoor temperature
        profiles for each thermal zone from the `global_mpc_problem`'s variables.
        It then formats these into Pandas DataFrames.

        Args:
            global_mpc_problem: The solved CVXPY Problem object.
            devices: A list of device dictionaries, used to order thermal zones.
            interval: The time step interval in minutes.

        Returns:
            A tuple containing two Pandas DataFrames:
            - `results_space_heating`: Contains the raw heater power and temperature profiles.
            - `control_space_heating`: Contains the temperature setpoint control signals
                                       mapped to thermal zone entity IDs.
        """
        # Order devices using priorities and filter for space heating
        devices = DeviceHelper.sort_devices_by_priorities(
            space_heating=True,
            electric_storage=False,
            electric_vehicle=False,
            water_heater=False,
        )
        # Build an order for thermal zones
        thermal_zones_ordered = []
        for tz in devices:
            thermal_zones_ordered.append(tz["entity_id"])

        # Build columns for the dataframes
        setpoint_columns = [
            "setpoint_" + entity_id for entity_id in thermal_zones_ordered
        ]
        power_columns = ["power_" + entity_id for entity_id in thermal_zones_ordered]

        # Build index
        date_range = pd.date_range(
            start=self.start,
            end=self.stop,
            freq=f"{interval}min",
        )[:-1]  # Remove the last timestamp
        # Initialize DataFrames
        control_df = pd.DataFrame(columns=power_columns, index=date_range)
        states_df = pd.DataFrame(columns=setpoint_columns, index=date_range)

        # Extract variable names and values from the global_mpc_problem
        for variable in global_mpc_problem.variables():
            # Assuming var has a name and a value method
            if variable.name() == "smart_thermostats_u_heaters":
                var_array = np.around(variable.value.T, 3)
                control_df = pd.DataFrame(
                    data=var_array, columns=power_columns, index=date_range
                )
            elif variable.name() == "smart_thermostats_x_temperature":
                var_array = np.around(variable.value.T, 3)
                states_df = pd.DataFrame(
                    data=var_array, columns=setpoint_columns, index=date_range
                )

        # Create the final DataFrame
        results_space_heating = pd.concat([control_df, states_df], axis=1)
        columns = [entity_id for entity_id in thermal_zones_ordered]
        values = []
        for name in range(len(columns)):
            values.append(
                results_space_heating["setpoint_" + thermal_zones_ordered[name]].values
            )

        # Fix dimensions for the values
        data = np.array(values).T

        control_space_heating = pd.DataFrame(
            data=data, columns=columns, index=date_range
        )
        return results_space_heating, control_space_heating

    def save_results_to_influxdb(self, results: pd.DataFrame) -> None:
        """Saves the results to InfluxDB."""
        # This method is not used in the current implementation, as saving is handled
        # within the `interpret` method for each device type.
        pass
