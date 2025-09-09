import os
from datetime import datetime
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
import pvlib

from cold_pickup_mpc.devices.device_mpc import DeviceMPC
from cold_pickup_mpc.retrievers.pv_retriever import (
    PhotovoltaicGeneratorDataRetriever,
)


class PhotovoltaicGeneratorMPC(DeviceMPC):
    """
    Mathematical representation for the photovoltaic generator device.

    This class computes the generation of the PV generator for the user.

    ### 1. Objective
    The PV module does not have an optimization objective.

    ### 2. Constraints
    The PV module does not have any constraints.

    ### 3. Dispatch
    The output power `D_{PV,t}` of `n^{PV}` photovoltaic panels is described as:
    $D^{PV}_{t} = n^{PV} {df}^{PV} P^{STC} (1+C^{PV,T}(T^{PV, W}_{t}-T^{STC})) {G^{A}_{t}}/{G^{STC}}$

    The working temperature `T^{PV, W}_{t}` is a function of the ambient temperature and incident solar radiation:
    $T^{PV, W}_{t} = T^{A}_{t} + (T^{NOCT}-T^{a,NOCT}_{t}) {G^{A}_{t}}/ {G^{NOCT}}$

    For simplification, we assume the installed PV capacity increases in kW, implying `n^{PV} * P^{STC} = 1` kW and a derating factor of 1.
    The simplified dispatch equation is:
    $D^{PV}_{t} = (1+C^{PV,T}(T^{PV, W}_{t}-T^{STC})) {G^{A}_{t}}/{G^{STC}}$

    ### 4. Optimization Variables
    The PV module does not have optimization variables.

    ### 5. Variable Names
    - `$df^{PV}$`: derating factor (unitless)
    - `$P^{STC}$`: output power of the PV module (kW)
    - `$G^{A,t}$`: GHI (kW/m^2)
    - `$G^{STC}$`: GHI at standard conditions (kW/m^2)
    - `$C^{PV,T}$`: Temperature coefficient of the PV module (%/°C)
    - `$T^{C,t}$`: working temperature of the PV cell at hour `t` (°C)
    - `$T^{STC}$`: temperature at standard conditions (°C)
    - `$G_{NOCT}$`: solar radiation (kW/m^2)
    - `$T_{NOCT}$`: working temperature (°C)
    - `$T_{a,t,NOCT}$`: ambient temperature (°C)

    NOCT variables refer to Nominal Operational Cell Temperature conditions.
    """

    def __init__(
        self,
        devices: List[Dict[str, Any]],
    ) -> None:
        """Initializes the PhotovoltaicGeneratorMPC.

        Args:
            devices: A list of dictionaries, where each dictionary contains the
            configuration and parameters of a photovoltaic generator.
        """
        self._pv_retriever = PhotovoltaicGeneratorDataRetriever(devices)

    def create_mpc_formulation(
        self,
        start: datetime,
        stop: datetime,
        steps_horizon_k: int,
        interval: int = 10,
        norm_factor: int = 1,
    ) -> Tuple[List, List, np.ndarray]:
        # Load device information and retrieve data
        device_dict = self._pv_retriever.retrieve_data(start, stop)

        # Define optimization objective
        objective: List = []

        # Define optimization constraints
        constraints: List = []

        dispatch = self.get_dispatch(start, stop, steps_horizon_k, device_dict)

        return objective, constraints, dispatch

    def get_dispatch(
        self,
        start: datetime,
        stop: datetime,
        steps_horizon_k: int,
        device_dict: Dict[str, Any],
    ) -> np.ndarray:
        # Load pv module
        # Get the absolute path to the database directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        database_path = os.path.join(current_dir, "..", "database")

        # Load pv module
        modules_path = os.path.join(database_path, "pvlib_cec_modules.csv")
        pv_module_name = device_dict["pv_module"]["rooftop_photovoltaic_panels"]
        pv_module_data = pvlib.pvsystem.retrieve_sam(path=modules_path)[pv_module_name]

        # Load inverter
        inverter_path = os.path.join(database_path, "pvlib_cec_inverters.csv")
        inverter_name = device_dict["inverter"]["rooftop_photovoltaic_panels"]
        inverter_data = pvlib.pvsystem.retrieve_sam(path=inverter_path)[inverter_name]

        # Load number of strings for the system
        modules_per_string = device_dict["modules_per_string"][
            "rooftop_photovoltaic_panels"
        ]
        strings_per_inverter = device_dict["strings_per_inverter"][
            "rooftop_photovoltaic_panels"
        ]

        # Define location (use floats here to avoid incompatibility type issues!)
        location = pvlib.location.Location(
            latitude=float(os.getenv("LATITUDE")),
            longitude=float(os.getenv("LONGITUDE")),
            tz=os.getenv("TIMEZONE"),
            altitude=float(os.getenv("ALTITUDE")),
        )

        # Build the PV system
        pv_system = pvlib.pvsystem.PVSystem(
            module_parameters=pv_module_data,
            inverter_parameters=inverter_data,
            surface_tilt=device_dict["surface_tilt"]["rooftop_photovoltaic_panels"],
            strings_per_inverter=strings_per_inverter,
            modules_per_string=modules_per_string,
            racking_model="open_rack",
            module_type="glass_polymer",
        )

        pv_system = pvlib.modelchain.ModelChain(
            pv_system, location, aoi_model="no_loss", spectral_model="no_loss"
        )

        # Process data
        weather_forecasts = self._process_weather_for_pv(
            start, stop, device_dict, steps_horizon_k
        )

        # Ensure all weather data is numeric before running the model
        weather_forecasts = weather_forecasts.apply(pd.to_numeric, errors="coerce")

        # Compute the power generation
        pv_system.run_model(weather=weather_forecasts)

        # Define optimization dispatch
        # Make it negative for the energy balance (consume power from the grid (+), inject power to the grid (-))
        pv_production = pv_system.results.ac.fillna(0) / 1000  # convert W to kW

        # Build the dispatch (dispatch is already negative, because it produces energy)
        pv_dispatch = np.array([pv_production.values])[:, 0:steps_horizon_k]

        return pv_dispatch

    def _process_weather_for_pv(
        self,
        start: datetime,
        stop: datetime,
        device_dict: Dict[str, Any],
        steps_horizon_k: int,
    ) -> pd.DataFrame:
        """Processes raw device data into a pandas DataFrame for the PV model.

        This helper function takes the dictionary of weather data and converts it
        into a pandas DataFrame with a DatetimeIndex. This format is required
        by the pvlib library.

        Args:
            start: The start time of the optimization horizon.
            stop: The end time of the optimization horizon.
            device_dict: A dictionary containing the raw weather data.
            steps_horizon_k: The number of time steps in the optimization horizon.

        Returns:
            A pandas DataFrame with weather data, indexed by timestamp.
        """
        # Create a DataFrame from the weather data
        weather_forecasts = pd.DataFrame(
            index=pd.to_datetime(list(device_dict["ghi"].keys()))
        )
        weather_forecasts.index.name = "timestamp"

        # Weather variables
        try:
            weather_forecasts["ghi"] = [float(v) for v in device_dict["ghi"].values()]
            weather_forecasts["dhi"] = [float(v) for v in device_dict["dhi"].values()]
            weather_forecasts["dni"] = [float(v) for v in device_dict["dni"].values()]
            weather_forecasts["temp_air"] = [
                float(v) for v in device_dict["temperature"].values()
            ]
            weather_forecasts["wind_speed"] = [
                float(v) for v in device_dict["wind_speed"].values()
            ]
        except ValueError as e:
            raise TypeError(f"All weather values must be numeric: {e}")

        # Validate the dataframe to respect the start and stop limits
        weather_forecasts = weather_forecasts.loc[start:stop]

        return weather_forecasts
