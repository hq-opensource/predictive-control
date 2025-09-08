import logging
import os
from datetime import datetime, timedelta

import pandas as pd
import pvlib

logger = logging.getLogger(__name__)


class PhotovoltaicManager:
    """

    Takes consumption historic data and use it to create a forecast of the consumption.

    """

    def __init__(self, config: dict, influx_manager_local: InfluxManager) -> None:
        self._influx_manager_local = influx_manager_local

        # Config

        self.photovoltaic_buckets = config.get("Buckets", None)

        self.photovoltaic_measurements = config.get("Measurements", None)

        self.photovoltaic_fields = config.get("Fields", None)

        self.photovoltaic_model_forecaster = config.get("ModelForecaster", None)

        self.photovoltaic_system_parameters = config.get("PVSystemParameters", None)

    def compute_and_save_photovoltaic_forecast(self, now: datetime) -> None:
        control_horizon = int(
            self.photovoltaic_model_forecaster.get("ControlHorizonInHours", 24)
            * (
                60
                / self.photovoltaic_model_forecaster.get("ControlTimestepInMinutes", 5)
            )
        )

        weather_forecats = self._retrieve_weather_forecast(
            now=now, control_horizon=control_horizon
        )

        weather_forecats = weather_forecats.rename(
            columns={
                "temperature": "temp_air",
                "solarGHI": "ghi",
                "solarDNI": "dni",
                "solarDHI": "dhi",
                "windSpeed": "wind_peed",
            }
        ).tz_convert("utc")  # .reset_index(drop=True)

        pv_model = self._create_pv_model()

        pv_model.run_model(weather=weather_forecats)

        pv_power_ac_forecats_kW_series = pv_model.results.ac.fillna(0)

        pv_power_ac_forecats_kW_series[pv_power_ac_forecats_kW_series < 0] = 0

        pv_power_ac_forecats_kW = pv_power_ac_forecats_kW_series.to_frame(
            name=self.photovoltaic_fields.get("photovoltaic_power_generation_ac", None)
        )

    def _retrieve_weather_forecast(
        self, now: datetime, control_horizon: int
    ) -> pd.DataFrame:
        currentTime = now.replace(second=0, microsecond=0)

        currentTime = currentTime - timedelta(
            minutes=int(
                currentTime.minute
                % self.photovoltaic_model_forecaster.get("ControlTimestepInMinutes", 5)
            )
        )

        start = currentTime

        stop = start + timedelta(
            hours=int(
                self.photovoltaic_model_forecaster.get("ControlHorizonInHours", 24) + 2
            )
        )

        fields_weather_to_ask = [
            self.photovoltaic_fields.get("solar_ghi", None),
            self.photovoltaic_fields.get("solar_dni", None),
            self.photovoltaic_fields.get("solar_dhi", None),
            self.photovoltaic_fields.get("temperature", None),
            self.photovoltaic_fields.get("wind_speed", None),
        ]

        weather_forecast = self._influx_manager_local.read(
            start=start,
            stop=stop,
            msname=self.photovoltaic_measurements.get("ms_weather_shawinigan", None),
            fields=fields_weather_to_ask,
            bucket=self.photovoltaic_buckets.get("bucket_weather_local", None),
            aggregate=int(
                60
                * self.photovoltaic_model_forecaster.get("ControlTimestepInMinutes", 5)
            ),
        )

        weather_forecast = weather_forecast.tz_convert("America/Montreal").round(
            2
        )  # head(control_horizon)

        return weather_forecast

    def _create_pv_model(self) -> None:
        pv_module = pvlib.pvsystem.retrieve_sam(
            path=os.getenv("PVLIB_MODULES_FILE_PATH", "config/pvlib_cec_modules.csv")
        )["Canadian_Solar_Inc__CS6K_280M"]

        inverter = pvlib.pvsystem.retrieve_sam(
            path=os.getenv(
                "PVLIB_INVERTERS_FILE_PATH", "config/pvlib_cec_inverters.csv"
            )
        )["Schneider_Electric_Solar_Inc___XW_Pro_6848_NA__240V_"]

        pv_system = pvlib.pvsystem.PVSystem(
            module_parameters=pv_module,
            inverter_parameters=inverter,
            surface_tilt=self.photovoltaic_system_parameters.get("surface_tilt"),
            strings_per_inverter=self.photovoltaic_system_parameters.get(
                "strings_per_inverter"
            ),
            modules_per_string=self.photovoltaic_system_parameters.get(
                "modules_per_string"
            ),
            racking_model=self.photovoltaic_system_parameters.get("racking_model"),
            module_type="glass_polymer",
        )

        # surface_azimuth = self.photovoltaic_system_parameters.get("surface_azimuth"),

        # surface_type = self.photovoltaic_system_parameters.get("surface_type"), #! Default or not?

        pv_model = pvlib.modelchain.ModelChain(
            pv_system, location, aoi_model="no_loss", spectral_model="no_loss"
        )

        return pv_model
