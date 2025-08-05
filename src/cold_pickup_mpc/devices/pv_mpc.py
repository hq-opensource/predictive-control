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
    """Mathematical representation for the photovoltaic generator device.

    Computes the generation of the PV generator of the user. It uses the following formulation:

    1.  Objective:

        The PV module does not have an optimization objective.

    2.  Constraints:

        The PV module does not have constraints.

    3.  Dispatch:

        References `[Li2017]`_, `[Zhang2016]`_, `[lasnier1990]`_ describe the output power :math:`D_{PV,t}` of a
        :math:`n^{PV}` number of photovoltaic panels as:

        ..  math::
            D^{PV}_{t} = n^{PV} {df}^{PV} P^{STC} (1+C^{PV,T}(T^{PV, W}_{t}-T^{STC})) {G^{A}_{t}}/{G^{STC}}
            :label: eq_pv_disp_1

        Reference [Skoplaki2009]_ describes :math:`T^{PV, W}_{t}` as a function of the ambient temperature and
        incident solar radiation over the PV module:

        .. math::
            T^{PV, W}_{t} = T^{A}_{t} + (T^{NOCT}-T^{a,NOCT}_{t}) {G^{A}_{t}}/ {G^{NOCT}}
            :label: eq_pv_disp_2

        Nevertheless, to simplify the computation we assumed that the capacity of installed PV increases in kW.
        Which implies that :math:`n^{PV}` multiplied by :math:`P^{STC}` it is equal to one kW. The derating factor
        is assumed to be 1. Thus, :eq:`eq_pv_disp_1` could be re-written as:

        ..  math::
            D^{PV}_{t} = (1+C^{PV,T}(T^{PV, W}_{t}-T^{STC})) {G^{A}_{t}}/{G^{STC}}
            :label: eq_pv_disp_3

    4.  Optimization variables:

        The PV module does not have optimization variables.


    5. Variable names

        :math:`{df}^{PV}` = derating factor (unitless)

        :math:`P^{STC}`, =  output power  of the PV module (:math:`kW`)

        :math:`G^{A,t}`, = GHI (:math:`kW/m^2`)

        :math:`G^{STC}`, = GHI at standard conditions (:math:`kW/m^2`)

        :math:`C^{PV,T}` = Temperature coefficient of the PV module (:math:`\%/^{\circ}C`)

        :math:`T^{C,t}`  is the working temperature of the PV cell at hour :math:`t` (:math:`^{\circ}C`)

        :math:`T^{STC}` is the temperature at standard conditions (:math:`^{\circ}C`)

        :math:`G_{NOCT}` = solar radiation (:math:`kW/m^2`)

        :math:`T_{NOCT}` = working temperature (:math:`^{\circ}C`)

        :math:`T_{a,t,NOCT}` = ambient temperature (:math:`^{\circ}C`)

        NOCT variables refer to Nominal Operational Cell Temperature (NOCT) conditions [Duffie2013]_, [librosolar]_.

    """

    def __init__(
        self,
        devices: List[Dict[str, Any]],
    ) -> None:
        """Initializes the PhotovoltaicGeneratorMPC.

        Args:
            devices: A list of dictionaries, where each dictionary contains the
                     configuration and parameters of an electric storage device.
        """
        self._pv_retriever = PhotovoltaicGeneratorDataRetriever(devices)

    def create_mpc_formulation(
        self,
        start: datetime,
        stop: datetime,
        steps_horizon_k: int,
        interval: int,
    ) -> Tuple[List, List, np.ndarray]:
        # Load device information and retrieve data
        device_dict = self._pv_retriever.retrieve_data(start, stop)

        # Load inverter
        inverter = device_dict["inverter"]
        self.inverter = pvlib.pvsystem.retrieve_sam("cecinverter")[inverter]

        # Load pv module
        pv_module = device_dict["pv_module"]
        self.pv_module_reference = pvlib.pvsystem.retrieve_sam("cecmod")[pv_module]

        # Load number of strings for the system
        self.strings_per_inverter = device_dict["strings_per_inverter"]
        self.modules_per_string = device_dict["modules_per_string"]

        # Define optimization objective
        objective: List = []

        # Define optimization constraints
        constraints: List = []

        dispatch = self.get_dispatch(start, stop, steps_horizon_k)

        return objective, constraints, dispatch

    def get_dispatch(
        self, start: datetime, stop: datetime, steps_horizon_k: int
    ) -> np.array:
        # Build PV system
        pv_system_configuration = pvlib.pvsystem.PVSystem(
            module_parameters=self.pv_module_reference,
            inverter_parameters=self.inverter,
            surface_tilt=os.getenv("LATITUDE"),
            strings_per_inverter=self.strings_per_inverter,
            modules_per_string=self.modules_per_string,
            racking_model="open_rack",
            module_type="glass_polymer",
        )

        location = pvlib.location.Location(
            latitude=os.getenv("LATITUDE"),
            longitude=os.getenv("LONGITUDE"),
            tz=os.getenv("TIMEZONE"),
            altitude=os.getenv("ALTITUDE"),
        )

        chain = pvlib.modelchain.ModelChain(
            pv_system_configuration, location, aoi_model="ashrae"
        )

        # Process data
        pv_arrays = self._process_data_as_arrays()

        # Load external variables
        pv_arrays = self._process_data_as_arrays(pv_info, steps_horizon_k)

        # Create weather vector to compute pv generation
        weather = pd.DataFrame(index=daily_data.weather_forecast.index)
        weather["ghi"] = pv_arrays["ghi"]
        weather["dni"] = pv_arrays["dni"]
        weather["dhi"] = pv_arrays["dhi"]

        # Compute the power generation
        chain.run_model(weather=weather)

        # Define optimization dispatch
        # Make it negative for the energy balance (consume power from the grid (+), inject power to the grid (-))
        pv_production = chain.results.ac.fillna(0) / 1000  # convert W to kW
        return np.array([-pv_production.values])

    def _process_data_as_arrays(
        self, pv_info: Dict[str, Any], steps_horizon_k: int
    ) -> Dict[str, np.ndarray]:
        """Processes raw device data into NumPy arrays for the optimization model.

        This helper function takes the dictionary of data retrieved for the electric
        storage device and converts it into a structured dictionary of NumPy arrays.
        This format is required by the CVXPY optimization problem. It handles unit
        conversions (e.g., SoC from % to kWh) and validates the initial state
        against the defined SoC limits.

        Args:
            pv_info: A dictionary containing the raw data and parameters
                                   for the electric storage device.
            steps_horizon_k: The number of time steps in the optimization horizon.

        Returns:
            A dictionary where keys are parameter names (e.g., 'initial_state',
            'power_capacity') and values are the corresponding NumPy arrays.
        """
        pv_arrays = {}

        # Weather variables
        pv_arrays["ghi"] = pv_info["ghi"]["pv"]
        pv_arrays["dni"] = pv_info["dni"]["pv"]
        pv_arrays["dhi"] = pv_info["dhi"]["pv"]

        return pv_arrays
