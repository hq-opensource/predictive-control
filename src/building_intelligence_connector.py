"""
Building Intelligence Connector
Bridges PREDICTIVE-CONTROL with Building Intelligence Core-API
Fetches device config, runs EV MPC optimization, sends schedules back
"""

# test

import sys
from pathlib import Path
import requests
import pandas as pd
from datetime import datetime, timedelta, timezone
import time
import cvxpy

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from cold_pickup_mpc.devices.electric_vehicle_v1g_mpc import ElectricVehicleV1GMPC
from cold_pickup_mpc.util.logging import LoggingUtil

logger = LoggingUtil.get_logger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

CORE_API_URL = "http://localhost:8080"
DEVICE_ID = "evduty_borne_evduty_evc30_17286_meeb1_max_amp"
PRIORITY = 50  # Schedule priority (0-100)
UPDATE_INTERVAL = 60*15  # seconds 

# MPC Settings
HORIZON_HOURS = 4  # Start with 4 hours like the working test
INTERVAL_MINUTES = 15  # Use 15-minute intervals (more reasonable than 1-min)

# ============================================================================
# API CLIENT FUNCTIONS
# ============================================================================

def get_device_config():
    """Fetch device configuration from Building Intelligence"""
    try:
        response = requests.get(f"{CORE_API_URL}/devices/", timeout=5)
        response.raise_for_status()
        data = response.json()
        
        # API returns {"content": [devices...]}
        devices = data.get("content", data) if isinstance(data, dict) else data
        
        # Find our EV charger
        for device in devices:
            if device.get("entity_id") == DEVICE_ID:
                logger.info(f"Device config loaded: {device.get('friendly_name')}")
                return device
        
        raise ValueError(f"Device {DEVICE_ID} not found")
    
    except Exception as e:
        logger.error(f"Error fetching device config: {e}")
        return None


def get_current_state():
    """Fetch current device state from Building Intelligence"""
    try:
        response = requests.get(
            f"{CORE_API_URL}/devices/state/{DEVICE_ID}",
            timeout=5
        )
        response.raise_for_status()
        current_amps = response.json()
        logger.info(f"Current charging rate: {current_amps} A")
        return current_amps
    
    except Exception as e:
        logger.error(f"Error fetching device state: {e}")
        return None


def send_schedule(schedule_dict):
    """Send optimized schedule to Building Intelligence"""
    try:
        url = f"{CORE_API_URL}/devices/schedule/{PRIORITY}"  # Priority in URL!
        payload = {DEVICE_ID: schedule_dict}  # Device ID as key!
        
        logger.info(f"Sending schedule to {url} with {len(schedule_dict)} setpoints")
        
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        
        logger.info(f"Schedule sent successfully: {response.status_code}")
        return True
    
    except Exception as e:
        logger.error(f"Error sending schedule: {e}")
        return False


# ============================================================================
# MPC PREPARATION
# ============================================================================

def prepare_device_info(device_config):
    """
    Convert Building Intelligence device config to MPC format
    
    Args:
        device_config: Device from Building Intelligence API
    
    Returns:
        List[Dict]: Device info in ElectricVehicleV1GMPC format
    """
    
    # Your MPC expects a list with one device dict
    device_info = [{
        "entity_id": device_config["entity_id"],
        "friendly_name": device_config["friendly_name"],
        "type": device_config["type"],
        
        # Required parameters
        "energy_capacity": device_config["energy_capacity"],  # 75000 Wh
        "power_capacity": device_config["power_capacity"],    # 7200 W
        "priority": device_config["priority"],                # 1.0
        
        # Optional parameters (use MPC defaults if null)
        "charging_efficiency": device_config.get("charging_efficiency"),
        "min_residual_energy": device_config.get("min_residual_energy"),
        "max_residual_energy": device_config.get("max_residual_energy"),
        "desired_state": device_config.get("desired_state"),
    }]
    
    return device_info


def prepare_v1g_info(device_config, num_steps):
    """
    Prepare v1g_info dictionary for MPC
    
    Args:
        device_config: Device configuration
        num_steps: Number of time steps in optimization horizon
    
    Returns:
        Dict[str, pd.DataFrame]: v1g_info with initial_state and branched_profile
    """
    
    # Initial SOC - Start low like the working test (25% = 18,750 Wh)
    energy_capacity = device_config["energy_capacity"]
    initial_soc = 0.25 * energy_capacity  # 18750 Wh for 75kWh battery (25%)
    
    logger.info(f"Using initial SOC: {initial_soc} Wh ({initial_soc/energy_capacity*100:.1f}%)")
    
    # Initial state DataFrame
    initial_state_df = pd.DataFrame({
        'initial_soc': [initial_soc]
    })
    
    # Connection schedule - For now, assume always connected (all 1s)
    branched_profile_df = pd.DataFrame({
        'connected': [1] * num_steps
    })
    
    logger.info(f"Connection profile: Always connected ({num_steps} steps)")
    
    v1g_info = {
        'initial_state': initial_state_df,
        'branched_profile': branched_profile_df
    }
    
    return v1g_info


# ============================================================================
# MPC OPTIMIZATION
# ============================================================================

def run_ev_mpc_optimization(device_config):
    """
    Run EV MPC optimization using your ElectricVehicleV1GMPC class
    
    Args:
        device_config: Device configuration from Building Intelligence
    
    Returns:
        dict: Schedule {timestamp_iso: setpoint_in_amps} or None if failed
    """
    
    try:
        # Prepare time window
        start = datetime.now(timezone.utc).replace(second=0, microsecond=0)
        stop = start + timedelta(hours=HORIZON_HOURS)
        interval = INTERVAL_MINUTES
        
        num_steps = int((stop - start).total_seconds() / 60 / interval)
        
        logger.info(f"Optimization horizon: {start} to {stop}")
        logger.info(f"Interval: {interval} min, Steps: {num_steps}")
        
        # Prepare device info for MPC
        device_info = prepare_device_info(device_config)
        
        # Prepare v1g_info
        v1g_info = prepare_v1g_info(device_config, num_steps)
        
        # Create MPC instance
        logger.info("Creating ElectricVehicleV1GMPC instance...")
        ev_mpc = ElectricVehicleV1GMPC(device_info)
        
        # Run optimization
        logger.info("Running MPC optimization...")
        objectives, constraints, dispatch_var = ev_mpc.create_mpc_formulation(
            start=start,
            stop=stop,
            interval=interval,
            v1g_info=v1g_info
        )
        
        # After: objectives, constraints, dispatch_var = ev_mpc.create_mpc_formulation(...)

        logger.info("Solving MPC optimization problem...")

        # 1. Create the optimization problem (objectives[0] is already complete!)
        problem = cvxpy.Problem(
            cvxpy.Minimize(objectives[0]),  # Don't sum! It's already a scalar expression
            constraints
        )

        # 2. Solve it!
        solve_start = datetime.now()
        problem.solve(verbose=False)
        solve_time = (datetime.now() - solve_start).total_seconds()

        # 3. Check if solution found
        if problem.status not in ["optimal", "optimal_inaccurate"]:
            logger.error(f"   Optimization failed with status: {problem.status}")
            logger.error(f"   Problem value: {problem.value}")
            logger.error(f"   Horizon: {num_steps} steps ({HORIZON_HOURS}h @ {INTERVAL_MINUTES}min intervals)")
            logger.error(f"   Initial SoC: {v1g_info['initial_state'].iloc[0, 0]} Wh")
            logger.error(f"   Energy capacity: {device_info[0]['energy_capacity']} Wh")
            return None

        # 4. Extract optimal charging power (W)
        optimal_power_w = dispatch_var.value.flatten()  # Shape: (1, 1440)

        logger.info(f"Optimization successful! Status: {problem.status}")
        logger.info(f"Optimal cost: {problem.value:.2f}")
        
        # PLACEHOLDER: Generate simple schedule for testing
        optimal_amps = optimal_power_w / 240.0
        schedule = {}
        current_time = start
        for i in range(len(optimal_amps)):  # Just 60 minutes for testing
            timestamp_str = current_time.strftime('%Y-%m-%dT%H:%M:%SZ')
            amp_value = float(optimal_amps[i])  # Convert numpy float to Python float
            schedule[timestamp_str] = amp_value
            current_time += timedelta(minutes=INTERVAL_MINUTES)

        logger.info(f"Generated {len(schedule)} setpoints")
        
        return schedule
    
    except Exception as e:
        logger.error(f"Error in MPC optimization: {e}", exc_info=True)
        return None


# ============================================================================
# MAIN LOOP
# ============================================================================

def main():
    """Main control loop"""
    
    logger.info("=" * 70)
    logger.info("EV Charging MPC Controller Started")
    logger.info(f"Core API: {CORE_API_URL}")
    logger.info(f"Device: {DEVICE_ID}")
    logger.info(f"Update interval: {UPDATE_INTERVAL} seconds")
    logger.info(f"Optimization horizon: {HORIZON_HOURS} hours")
    logger.info("=" * 70)
    
    iteration = 0
    
    while True:
        iteration += 1
        logger.info("")
        logger.info("=" * 70)
        logger.info(f"Iteration {iteration} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 70)
        
        try:
            # 1. Fetch device configuration
            logger.info(" Fetching device configuration...")
            device_config = get_device_config()
            if not device_config:
                logger.warning("Failed to get device config, retrying in 60s...")
                time.sleep(UPDATE_INTERVAL)
                continue
            
            # 2. Fetch current state (optional, for logging)
            logger.info(" Fetching current device state...")
            current_state = get_current_state()
            
            # 3. Run MPC optimization
            logger.info(" Running EV MPC optimization...")
            schedule = run_ev_mpc_optimization(device_config)
            
            if not schedule:
                logger.error("MPC optimization failed")
                time.sleep(UPDATE_INTERVAL)
                continue
            
            # 4. Send schedule to Building Intelligence
            logger.info(" Sending schedule to Building Intelligence...")
            success = send_schedule(schedule)
            
            if success:
                logger.info("Optimization cycle completed successfully!")
            else:
                logger.warning("Failed to send schedule")
        
        except Exception as e:
            logger.error(f"Error in optimization cycle: {e}", exc_info=True)
        
        # Wait for next iteration
        logger.info(f" Waiting {UPDATE_INTERVAL} seconds until next optimization...")
        time.sleep(UPDATE_INTERVAL)


if __name__ == "__main__":
    main()
