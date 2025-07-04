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

THERMAL_MODEL_SAVE_DIR = "/app/data/thermal_models"


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
        if (
            bool(internal_states_dict)
            and bool(control_variables_dict)
            and bool(external_variables_dict)
        ):
            logger.info(
                "Historic data found. Learning thermal model from historic data."
            )
            # Process historic data
            x_internal_states, u_control_variables, w_external_variables = (
                self._process_dict_data_for_learning(
                    internal_states_dict,
                    control_variables_dict,
                    external_variables_dict,
                )
            )
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
                zones = x_internal_states.shape[1]
                thermal_model_dict = {
                    "thermal_zones": zones,
                    "x_internal_states": user_thermal_model["Ax"],
                    "u_heaters": user_thermal_model["Au"],
                    "w_external_variables": user_thermal_model["Aw"],
                    "saved_date": datetime.now().astimezone().isoformat(),
                }
                self._save_thermal_model_to_json(thermal_model_dict)
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

        # Retrieve internal states (temperature)
        internal_states_dict = tz_temperature

        # Retrieve control variables
        control_variables_dict = tz_electric_consumption

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
        u_control_variables_df_neg = (
            u_control_variables_df * -1 / 1000
        )  # Positive consumption and change for kW
        u_control_variables_df_tz = u_control_variables_df_neg.clip(
            lower=0
        )  # Delete negative values

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

        x_internal_states = np.full((thermal_zones, thermal_zones), 0.02)
        np.fill_diagonal(x_internal_states, 0.98)

        u_heaters = np.full((thermal_zones, thermal_zones), 0)
        np.fill_diagonal(u_heaters, 0.02)

        w_external_variables = np.full((thermal_zones), 0)

        thermal_model = {
            "thermal_zones": thermal_zones,
            "x_internal_states": x_internal_states.tolist(),
            "u_heaters": u_heaters.tolist(),
            "w_external_variables": w_external_variables.tolist(),
            "saved_date": datetime.now().astimezone().isoformat(),
        }

        logger.info("Default thermal model created.")
        return thermal_model
