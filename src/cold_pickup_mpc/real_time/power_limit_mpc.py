import os
import threading
import time

from datetime import datetime
from typing import Any, Dict

from cold_pickup_mpc.devices.api_calls import retrieve_total_consumption, write_setpoint
from cold_pickup_mpc.devices.helper import DeviceHelper
from cold_pickup_mpc.retrievers.api_calls import retrieve_total_consumption, write_setpoint
from cold_pickup_mpc.util.logging import LoggingUtil


logger = LoggingUtil.get_logger(__name__)


class RealTimeControl(threading.Thread):
    """Class implementing Real-Time Control (RTC) to enforce power limits."""

    def __init__(
        self,
        power_limit: Dict[datetime, float],
        space_heating: bool,
        electric_storage: bool,
        electric_vehicle: bool,
        water_heater: bool,
    ) -> None:
        super().__init__()
        self._space_heating = space_heating
        self._electric_storage = electric_storage
        self._electric_vehicle = electric_vehicle
        self._water_heater = water_heater
        self.power_limit = power_limit
        self.must_run = True
        self.is_running = False

    def run(self) -> None:
        """Main control loop to enforce power limit in real-time."""
        logger.info("Starting Real-Time Control")
        self.is_running = True

        # Load and sort controllable devices
        devices = DeviceHelper.sort_devices_by_priorities(
            self._space_heating, self._electric_storage, self._electric_vehicle, self._water_heater
        )
        # Set last change to 60 seconds before starting
        devices_last_change = {}
        for device in devices:
            devices_last_change[device["entity_id"]] = time.time() - 60
        # Start real time control loop
        try:
            while self.must_run:
                try:
                    for device in devices:
                        # Check if curtailment is needed
                        if self._needs_curtailment():
                            # Aplly curtailment action
                            self._apply_curtailment_action(device, devices_last_change)
                        else:
                            logger.info(
                                "Total power %.2f kW within limit of %.2f, no action needed",
                                self._get_total_consumption(),
                                self._get_current_power_limit(datetime.now().astimezone()),
                            )
                    # If there are no more devices to curtail and consumption
                    # is still higher than limit trigger a user notification
                    self._trigger_notification()

                    time.sleep(float(os.getenv("MONITOR_INTERVAL", "1")))
                except Exception as ex:
                    logger.error("Error in Real Time Control loop: %s", ex, exc_info=True)
                    time.sleep(float(os.getenv("MONITOR_INTERVAL", "1")))
        finally:
            self.is_running = False

        logger.info("RTC stopped.")

    def _needs_curtailment(self) -> bool:
        """Check if total power exceeds the threshold (S^total_k > S^L_k - M_k)."""
        # Monitor total consumption
        total_power = self._get_total_consumption()  # S^total_k
        if total_power is None:
            logger.error("Failed to retrieve total consumption, skipping iteration")
            time.sleep(float(os.getenv("MONITOR_INTERVAL", "1")))
        else:
            logger.info("Real time consumption is %s", total_power)

        current_power_limit = self._get_current_power_limit(datetime.now().astimezone())
        if current_power_limit is None:
            logger.info("No applicable power limit found, stopping Real-Time control")
            self.must_run = False

        logger.info("Real-Time Control current power limit: %.2f kW", current_power_limit)
        security_limit = float(os.getenv("SECURITY_LIMIT", "0,5"))
        if current_power_limit < security_limit:
            threshold = current_power_limit
        else:
            threshold = current_power_limit - security_limit
        # Verify if current power limit is superior to the threshold
        needs_curtailment = total_power > threshold
        logger.info(
            "Net power: %.2f kW, Threshold: %.2f kW, Needs curtailment: %s", total_power, threshold, needs_curtailment
        )
        return needs_curtailment

    def _apply_curtailment_action(
        self,
        device: Dict[str, Any],
        devices_last_change: Dict[str, Any],
    ) -> None:
        """Apply curtailment to controllable loads."""
        if self._can_adjust_device(device, devices_last_change):
            devices_last_change = self._set_device_critical_action(device, devices_last_change)
        else:
            logger.debug("Debounce active for %s, skipping", device["entity_id"])

    def _set_device_critical_action(
        self, device: Dict[str, Any], devices_last_change: Dict[str, float]
    ) -> Dict[str, float]:
        """Set device critical action. This function is called only if curtailment is required."""
        write_setpoint(device["entity_id"], device["critical_action"])
        logger.info("Set setpoint to %s for device %s", device["critical_action"], device["entity_id"])
        devices_last_change[device["entity_id"]] = time.time()
        return devices_last_change

    def _can_adjust_device(self, device: Dict[str, float], devices_last_change: Dict[str, float]) -> bool:
        """Check if device can be adjusted based on debounce time."""
        entity_id = device["entity_id"]
        debounce_time = (
            float(os.getenv("DEBOUNCE_TIME_BATTERY", "30"))  # Measured in seconds
            if "battery" in entity_id.lower()
            else float(os.getenv("DEBOUNCE_TIME", "5"))  # Measured in seconds
        )
        elapsed = time.time() - devices_last_change[entity_id]
        return elapsed > debounce_time

    def _get_total_consumption(self) -> float | None:
        """Retrieve total consumption (S^total_k)."""
        # Add negative sign to make consumption positive and production negative
        total_power = self._get_average_total_consumption()
        if isinstance(total_power, float):
            total_power = -total_power
        return total_power if total_power is not None else None

    def _get_average_total_consumption(self) -> float | None:
        """Retrieve average total consumption from TimescaleDB."""
        try:
            total_consumption = retrieve_total_consumption()
            return total_consumption["total_consumption"]
        except Exception as e:
            logger.error("Database error: %s", e)
            return None

    def _trigger_notification(self) -> None:
        """Trigger user notification if curtailment is insufficient (Notify_k)."""
        total_power = self._get_total_consumption()
        current_power_limit = self._get_current_power_limit(datetime.now().astimezone())

        if total_power > current_power_limit:
            logger.warning(
                "No more loads to curtail, and the adjusted total power is still above the limit (%.2f kW > %.2f kW)",
                total_power,
                current_power_limit,
            )
            # Placeholder for notification logic (e.g., add endpoint on CoreAPI)

    def _get_current_power_limit(self, timestamp: datetime) -> float | None:
        last_limit = max(self.power_limit.keys())
        first_limit = min(self.power_limit.keys())

        # Check if we are before/after limits
        if last_limit < timestamp < first_limit:
            return None

        applicable_times = [t for t in self.power_limit.keys() if t <= timestamp]

        # We are *before* the first limit (should never happen, but just in case)
        if not applicable_times:
            return None

        # Get most recent applicable time
        latest_time = max(applicable_times)
        return self.power_limit[latest_time]
