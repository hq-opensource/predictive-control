import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, Tuple

import numpy as np
from pandas import DataFrame, to_datetime

from cold_pickup_mpc.devices.helper import DeviceHelper
from cold_pickup_mpc.retrievers.api_calls import (
    get_devices,
    get_historical_data,
    get_weather_historic,
)
from cold_pickup_mpc.thermal_model.thermal_models import ThermalModels
from cold_pickup_mpc.util.logging import LoggingUtil

logger = LoggingUtil.get_logger(__name__)

import pathlib
PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent.parent
THERMAL_MODEL_SAVE_DIR = os.getenv("THERMAL_MODEL_SAVE_DIR", str(PROJECT_ROOT / "data" / "thermal_models"))


class LearnThermalDynamics:
    """Manages the learning, validation, and persistence of thermal models for space heating.

    This class is responsible for:
    - Retrieving historical data (indoor temperature, heater consumption, weather)
      from the Core API.
    - Preprocessing this data for use in a thermal model learning algorithm.
    - Executing the learning process to derive a state-space thermal model.
    - Validating if an existing thermal model is up-to-date or if re-learning is required.
    - Saving and loading learned thermal models to/from a JSON file for persistence.
    - Providing a default thermal model if learning fails or insufficient data is available.
    """

    def __init__(self) -> None:
        """Initializes the LearnThermalDynamics by retrieving information about all devices."""
        # Retrieve information about all devices
        all_devices_dict = get_devices()
        self._devices = all_devices_dict["content"]

    def validate_or_learn_model(
        self, start: datetime, stop: datetime
    ) -> Dict[str, Any]:
        """Validates if a thermal model exists and is recent; otherwise, it learns a new one.

        This method checks for a saved thermal model. If found, it verifies if the model
        was learned within a `learning_threshold` (e.g., 1 day). If the model is missing,
        outdated, or cannot be loaded, it triggers the `execute_learning` process.

        Args:
            start: The start datetime for retrieving historical data if learning is needed.
            stop: The stop datetime for retrieving historical data if learning is needed.

        Returns:
            A dictionary containing the validated, newly learned, or default thermal model.
        """
        # Verify if the thermal model was learned recently
        learning_threshold = timedelta(days=1)

        try:
            loaded_thermal_model = self._load_thermal_model_from_json()
            if len(loaded_thermal_model) == 0:
                logger.info(
                    "Thermal model not found on the specified directory. Learning it now..."
                )
                thermal_model = self.execute_learning(start, stop, False)
            else:
                saved_date_str = loaded_thermal_model.get("saved_date", None)
                if saved_date_str is not None:
                    saved_date = datetime.fromisoformat(saved_date_str)
                    if datetime.now().astimezone() > saved_date + learning_threshold:
                        logger.info(
                            "Thermal model found from %s. Thermal models is older than %s.",
                            saved_date,
                            learning_threshold,
                        )
                        logger.info("Re-learning model...")
                        thermal_model = self.execute_learning(start, stop)
                    else:
                        logger.info(
                            "Thermal model found from %s. Thermal models is newer than %s.",
                            saved_date,
                            learning_threshold,
                        )
                        logger.info("Thermal model is still valid...")
                        thermal_model = loaded_thermal_model
                else:
                    logger.info("Impossible to find the date. Re-learning model...")
                    thermal_model = self.execute_learning(start, stop)
        except (FileNotFoundError, KeyError, TypeError, ValueError) as e:
            print(f"Error loading thermal model: {e}. Re-learning model...")
            thermal_model = self.execute_learning(start, stop)

        return thermal_model

    def execute_learning(
        self, start: datetime, stop: datetime, old_model_exists: bool = True
    ) -> Dict[str, Any]:
        """Executes the learning process for the thermal models.

        This method retrieves historical data, processes it, and then attempts
        to learn a black-box thermal model using the `ThermalModels` class.
        If learning fails (e.g., due to insufficient data or optimization issues),
        it provides either an existing old model or a default model.

        Args:
            start: The start datetime for retrieving historical data.
            stop: The stop datetime for retrieving historical data.
            old_model_exists: A boolean indicating if an old model was found,
                              used for logging purposes.

        Returns:
            A dictionary containing the learned thermal model parameters (Ax, Au, Aw)
            and metadata, or a default model if learning is unsuccessful.
        """
        # Add default for thermal model dict
        thermal_model_dict = {}

        # region to execute the learning of the new thermal model
        # Retrieve historic data
        logger.info("Retrieving historic data from the Core API.")
        internal_states_dict, control_variables_dict, external_variables_dict = (
            self._retrieve_historic_data(start, stop)
        )

        # Build flag to track learning
        learning_failed = False

        # Check if all dataframes are not empty
        any_data_missing = False
        if not internal_states_dict or any(not d for d in internal_states_dict.values()):
            logger.warning("Internal states historic data is empty or missing.")
            any_data_missing = True
        
        if not control_variables_dict or any(not d for d in control_variables_dict.values()):
            logger.warning("Control variables historic data is empty or missing.")
            any_data_missing = True
            
        if not external_variables_dict:
            logger.warning("External variables (weather) historic data is empty.")
            any_data_missing = True

        if not any_data_missing:
            logger.info(
                "Historic data found. Learning thermal model from historic data."
            )
            try:
                # Process historic data
                x_internal_states, u_control_variables, w_external_variables = (
                    self._process_dict_data_for_learning(
                        internal_states_dict,
                        control_variables_dict,
                        external_variables_dict,
                    )
                )
                
                if x_internal_states.empty or u_control_variables.empty or w_external_variables.empty:
                    logger.warning("Processed dataframes are empty. Cannot learn thermal model.")
                    learning_failed = True
                else:
                    # Create thermal model object
                    thermal_models = ThermalModels()

                    # Execute learning of thermal model
                    user_thermal_model = thermal_models.learn_black_model(
                        x_internal_states, u_control_variables, w_external_variables
                    )

                    # Create the RC model only if the results exist
                    if user_thermal_model is None:
                        logger.warning(
                            "Learners tried to solve the optimization problem and found an error."
                        )
                        learning_failed = True
                    else:
                        # Get canonical zone order (matches MPC ordering)
                        all_sh_devices = DeviceHelper.sort_devices_by_priorities(
                            space_heating=True,
                            electric_storage=False,
                            electric_vehicle=False,
                            water_heater=False,
                        )
                        all_eids = [d["entity_id"] for d in all_sh_devices]
                        learned_eids = list(x_internal_states.columns)
                        n_total = len(all_eids)
                        n_learned = len(learned_eids)

                        Ax_l = np.array(user_thermal_model["Ax"])
                        Au_l = np.array(user_thermal_model["Au"])
                        Aw_l = np.array(user_thermal_model["Aw"])

                        if n_learned < n_total:
                            # Pad missing zones with default diagonal values so
                            # the model always matches the full set of MPC zones.
                            missing = set(all_eids) - set(learned_eids)
                            logger.warning(
                                "Padding thermal model with default values for %d missing zone(s): %s",
                                len(missing), missing,
                            )
                            Ax_full = np.eye(n_total) * 0.98
                            Au_full = np.eye(n_total) * 0.02
                            Aw_full = np.full((n_total, 1), 0.02)
                            for i, eid_i in enumerate(all_eids):
                                if eid_i not in learned_eids:
                                    continue
                                li = learned_eids.index(eid_i)
                                Aw_full[i] = Aw_l[li]
                                for j, eid_j in enumerate(all_eids):
                                    if eid_j not in learned_eids:
                                        continue
                                    lj = learned_eids.index(eid_j)
                                    Ax_full[i, j] = Ax_l[li, lj]
                                    Au_full[i, j] = Au_l[li, lj]
                            Ax_save = Ax_full.tolist()
                            Au_save = Au_full.tolist()
                            Aw_save = Aw_full.tolist()
                        else:
                            Ax_save = Ax_l.tolist()
                            Au_save = Au_l.tolist()
                            Aw_save = Aw_l.tolist()

                        thermal_model_dict = {
                            "thermal_zones": n_total,
                            "x_internal_states": Ax_save,
                            "u_heaters": Au_save,
                            "w_external_variables": Aw_save,
                            "saved_date": datetime.now().astimezone().isoformat(),
                        }
                        self._save_thermal_model_to_json(thermal_model_dict)
            except Exception as e:
                logger.error("An unexpected error occurred during thermal learning: %s", str(e))
                learning_failed = True
        else:
            logger.warning(
                "Skipping the learning of the thermal models due to lack of historic data."
            )
            learning_failed = True

        if learning_failed:
            if old_model_exists:
                logger.warning("Providing old thermal model.")
            else:
                logger.warning("Providing default thermal model.")

            space_heating_devices = DeviceHelper.get_all_device_info_by_key(
                self._devices, "type", DeviceHelper.SPACE_HEATING.value
            )
            # Build default model
            thermal_model_dict = self._create_default_model_if_not_exists(
                len(space_heating_devices)
            )
            # Save default model
            self._save_thermal_model_to_json(thermal_model_dict)

        # endregion to execute the learning of the new thermal model

        return thermal_model_dict

    def _retrieve_historic_data(
        self, start: datetime, stop: datetime
    ) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
        """Retrieves historical data required for thermal model learning.

        This method fetches historical indoor temperatures, electric consumption
        of heaters, and outdoor weather temperature from the Core API for all
        configured space heating devices within the specified time range.

        Args:
            start: The start datetime for retrieving historical data.
            stop: The stop datetime for retrieving historical data.

        Returns:
            A tuple containing three dictionaries:
            - `internal_states_dict`: Historical indoor temperatures for each thermal zone.
            - `control_variables_dict`: Historical electric consumption of heaters for each thermal zone.
            - `external_variables_dict`: Historical outdoor temperature data.
        """
        # Get device info
        device = DeviceHelper.SPACE_HEATING.value
        devices_info = DeviceHelper.get_all_device_info_by_key(
            devices=self._devices, filter_key="type", filter_value=device
        )

        # Build dictionary for historic temperature of thermal zones
        tz_temperature = {}
        for device_dict in devices_info:
            tz_temperature[device_dict["entity_id"]] = get_historical_data(
                historic_type="tz-temperature",
                start=start,
                stop=stop,
                device_id=device_dict["entity_id"],
            )

        # Build dictionary for historic consumption of thermal zones
        tz_electric_consumption = {}
        for device_dict in devices_info:
            tz_electric_consumption[device_dict["entity_id"]] = get_historical_data(
                historic_type="tz-electric-consumption",
                start=start,
                stop=stop,
                device_id=device_dict["entity_id"],
            )

        # Filter out devices that are missing data in either temperature or consumption.
        # A single device with no data must not abort learning for all other zones.
        valid_devices = {
            eid for eid in tz_temperature
            if tz_temperature.get(eid) and tz_electric_consumption.get(eid)
        }
        skipped = set(tz_temperature.keys()) - valid_devices
        if skipped:
            logger.warning(
                "Skipping %d device(s) with missing historic data: %s",
                len(skipped),
                skipped,
            )

        # Retrieve internal states (temperature)
        internal_states_dict = {k: v for k, v in tz_temperature.items() if k in valid_devices}

        # Retrieve control variables
        control_variables_dict = {k: v for k, v in tz_electric_consumption.items() if k in valid_devices}

        # Retrieve external variables (weather)
        external_variables_dict = get_weather_historic("temperature", start, stop)

        return (internal_states_dict, control_variables_dict, external_variables_dict)

    def _process_dict_data_for_learning(
        self,
        internal_states_dict: Dict[str, Any],
        control_variables_dict: Dict[str, Any],
        external_variables: Dict[str, Any],
    ) -> Tuple[DataFrame, DataFrame, DataFrame]:
        """Processes raw historical data dictionaries into Pandas DataFrames for thermal model learning.

        This method converts the retrieved historical data into a structured format
        (Pandas DataFrames) suitable for the thermal model learning algorithm.
        It handles timezone conversions, unit conversions (e.g., Wh to kWh),
        and ensures all DataFrames share a common time range.

        Args:
            internal_states_dict: Dictionary of historical indoor temperatures.
            control_variables_dict: Dictionary of historical heater electric consumption.
            external_variables: Dictionary of historical outdoor temperature.

        Returns:
            A tuple containing three Pandas DataFrames:
            - `x_internal_states`: Processed internal states (indoor temperatures).
            - `u_control_variables`: Processed control variables (heater power).
            - `w_external_variables`: Processed external variables (outdoor temperature).
        """
        time_zone = os.getenv("TZ")

        # Prepare internal states
        internal_states_df = DataFrame.from_dict(internal_states_dict, orient="columns")
        internal_states_df.index = to_datetime(internal_states_df.index)
        internal_states_df_tz = internal_states_df.tz_convert(time_zone)

        # Prepare control variables
        u_control_variables_df = DataFrame.from_dict(
            control_variables_dict, orient="columns"
        )
        u_control_variables_df.index = to_datetime(u_control_variables_df.index)
        u_control_variables_df = u_control_variables_df.tz_convert(time_zone)
        # All eGauge PPSR channels write to InfluxDB in Watts (scale=1.0,
        # no per-channel conversion in the Telegraf modbus_processor).
        # Divide uniformly by 1000 to get kW for the MPC.
        # Clip to [0, 10] to remove sensor glitches (e.g. cuisine/salle_manger
        # spikes reaching hundreds of apparent Watts due to measurement noise).
        u_control_variables_df_tz = (u_control_variables_df / 1000.0).clip(lower=0, upper=10.0)

        # Prepare external variables
        w_external_variables_df = DataFrame.from_dict(
            {"temperature": external_variables}, orient="columns"
        )
        w_external_variables_df.index = to_datetime(w_external_variables_df.index)
        w_external_variables_df_tz = w_external_variables_df.tz_convert(time_zone)

        # region to verify all dataframes share same starting and ending dates.
        # Get start and end timestamps for each DataFrame
        start_times = [
            internal_states_df_tz.index[0],
            u_control_variables_df_tz.index[0],
            w_external_variables_df_tz.index[0],
        ]

        end_times = [
            internal_states_df_tz.index[-1],
            u_control_variables_df_tz.index[-1],
            w_external_variables_df_tz.index[-1],
        ]

        # Compute the common range
        common_start = max(start_times)
        common_end = min(end_times)

        # Trim all dataframes to the common time range
        internal_states_df_tz = internal_states_df_tz.loc[common_start:common_end]
        u_control_variables_df_tz = u_control_variables_df_tz.loc[
            common_start:common_end
        ]
        w_external_variables_df_tz = w_external_variables_df_tz.loc[
            common_start:common_end
        ]
        # region to verify all dataframes share same starting and ending dates.

        return (
            internal_states_df_tz,
            u_control_variables_df_tz,
            w_external_variables_df_tz,
        )

    def _save_thermal_model_to_json(self, info_to_save: Dict) -> None:
        """Saves a dictionary representing a thermal model to a local JSON file.

        The model is saved in two locations: a 'latest' file (overwritten on each save)
        and a timestamped file for historical traceability.

        Args:
            info_to_save: The dictionary containing the thermal model parameters and metadata.
        """
        # Define a consistent save directory inside the container

        os.makedirs(
            THERMAL_MODEL_SAVE_DIR, exist_ok=True
        )  # Create directory if it doesn’t exist
        file_path_latest = os.path.join(THERMAL_MODEL_SAVE_DIR, "latest")
        file_path_date = os.path.join(
            THERMAL_MODEL_SAVE_DIR,
            datetime.now()
            .replace(second=0, microsecond=0)
            .astimezone()
            .isoformat()
            .replace(":", "-"),
        )
        # Save latest file
        try:
            with open(file_path_latest, "w") as f:
                json.dump(info_to_save, f, indent=4)
            logger.debug("Info saved to %s", file_path_latest)
        except Exception as e:
            logger.error("Failed to save info to %s: %s", file_path_latest, str(e))

        # Save model with date for traceability
        try:
            with open(file_path_date, "w") as f:
                json.dump(info_to_save, f, indent=4)
            logger.debug("Info saved to %s", file_path_date)
        except Exception as e:
            logger.error("Failed to save info to %s: %s", file_path_date, str(e))

    def _load_thermal_model_from_json(self) -> Dict:
        """Loads the latest saved thermal model from a JSON file.

        Returns:
            A dictionary containing the loaded thermal model, or an empty dictionary
            if the file does not exist or an error occurs during loading.
        """
        file_path = os.path.join(THERMAL_MODEL_SAVE_DIR, "latest")
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.warning("Failed to load from %s: %s", file_path, str(e))
            return {}

    def _create_default_model_if_not_exists(self, thermal_zones: int) -> Dict[str, Any]:
        """Creates a default thermal model if no learned model exists.

        This method provides a fallback thermal model with predefined (though
        simplified) parameters. This ensures that the MPC can still operate
        even if the learning process fails or no historical data is available.

        Args:
            thermal_zones: The number of thermal zones for which to create the default model.

        Returns:
            A dictionary containing the default thermal model parameters.
        """
        file_path = os.path.join(THERMAL_MODEL_SAVE_DIR, "latest")
        if os.path.exists(file_path):
            logger.info(
                "Thermal model already exists. Skipping default model creation."
            )
            return self._load_thermal_model_from_json()

        # Stable diagonal model: each zone retains 98% of its heat per step.
        # Off-diagonal coupling is intentionally omitted so the row sum stays
        # below 1.0 (spectral radius < 1 → stable dynamics).
        x_internal_states = np.eye(thermal_zones) * 0.98

        u_heaters = np.full((thermal_zones, thermal_zones), 0.0)
        np.fill_diagonal(u_heaters, 0.02)

        # Non-zero outdoor coupling: each degree of outdoor temperature
        # contributes ~2% per step, giving the model a natural heat sink.
        w_external_variables = np.full((thermal_zones, 1), 0.02)

        thermal_model = {
            "thermal_zones": thermal_zones,
            "x_internal_states": x_internal_states.tolist(),
            "u_heaters": u_heaters.tolist(),
            "w_external_variables": w_external_variables.tolist(),
            "saved_date": datetime.now().astimezone().isoformat(),
        }

        logger.info("Default thermal model created.")
        return thermal_model
