"""End-to-end test for the Real-Time Controller (RTC).

This script verifies that the real-time controller can push control actions
to all four load categories — space heating, battery, water heater, and EV —
through the same code path that the production RTC uses.

Two complementary test modes are provided:

  1. --mode direct
     Calls write_setpoint() directly for every controllable device with its
     configured critical_action value.  This is the lowest-level verification:
     if the Core API accepts the call and Home Assistant executes it you'll see
     the changes in HA immediately.

  2. --mode rtc
     Instantiates a RealTimeControl thread with a power limit set to 0 kW so
     that _needs_curtailment() always returns True, forcing the RTC to dispatch
     critical actions to all devices.  The thread runs for a configurable
     duration (default 60 s) and then stops gracefully.  This exercises the
     full production code path including debounce logic.

  3. --mode restore
     Sends each device back to its activation_action (normal operation).

Usage examples
--------------
# From inside predictive-control/:
  uv run python test_real_time_control.py --mode status
  uv run python test_real_time_control.py --mode direct
  uv run python test_real_time_control.py --mode rtc --duration 60
  uv run python test_real_time_control.py --mode restore

Environment
-----------
Reads CORE_API_URL from the .env file in this directory (falls back to
http://localhost:8000).
"""

import argparse
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List

import requests
from dotenv import load_dotenv

# ── Load environment ──────────────────────────────────────────────────────────
load_dotenv()  # reads predictive-control/.env
CORE_API_URL = os.getenv("CORE_API_URL", "http://localhost:8000")

# ── Formatting helpers ────────────────────────────────────────────────────────
SEPARATOR = "=" * 70
SEP_SMALL = "-" * 70


def banner(title: str) -> None:
    print(f"\n{SEPARATOR}")
    print(f"  {title}")
    print(SEPARATOR)


def ok(msg: str) -> None:
    print(f"  ✅  {msg}")


def fail(msg: str) -> None:
    print(f"  ❌  {msg}")


def info(msg: str) -> None:
    print(f"  ℹ️   {msg}")


def warn(msg: str) -> None:
    print(f"  ⚠️   {msg}")


# ── Core API helpers ──────────────────────────────────────────────────────────

def check_api_connectivity() -> bool:
    """Return True if the Core API is reachable."""
    try:
        r = requests.get(f"{CORE_API_URL}/", timeout=5)
        return r.status_code < 500
    except Exception as exc:
        fail(f"Cannot reach Core API at {CORE_API_URL}: {exc}")
        return False


def get_devices() -> List[Dict[str, Any]]:
    """Fetch device list from Core API."""
    r = requests.get(f"{CORE_API_URL}/devices", timeout=10)
    r.raise_for_status()
    return r.json().get("content", [])


def get_device_state(device_id: str, field: str | None = None) -> Any:
    """Fetch the current state of a device from Core API."""
    params = {}
    if field:
        params["field"] = field
    r = requests.get(f"{CORE_API_URL}/devices/state/{device_id}", params=params, timeout=10)
    r.raise_for_status()
    return r.json()


def send_setpoint(device_id: str, setpoint: float) -> requests.Response:
    """POST a setpoint to the Core API (same call as write_setpoint in api_calls.py)."""
    r = requests.post(
        f"{CORE_API_URL}/devices/setpoint/{device_id}",
        params={"setpoint": setpoint},
        timeout=10,
    )
    r.raise_for_status()
    return r


# ── Device categorisation ─────────────────────────────────────────────────────

DEVICE_TYPE_LABELS = {
    "space_heating": "🔥 Space Heating",
    "electric_storage": "🔋 Battery",
    "water_heater": "💧 Water Heater",
    "electric_vehicle_v1g": "🚗 EV (V1G)",
    "on_off_ev_charger": "🚗 EV (On/Off charger)",
}

CONTROLLABLE_TYPES = set(DEVICE_TYPE_LABELS.keys())


def filter_controllable(
    devices: List[Dict[str, Any]],
    space_heating: bool,
    electric_storage: bool,
    electric_vehicle: bool,
    water_heater: bool,
) -> List[Dict[str, Any]]:
    """Return only the device types requested, sorted by priority."""
    wanted = set()
    if space_heating:
        wanted.add("space_heating")
    if electric_storage:
        wanted.add("electric_storage")
    if electric_vehicle:
        wanted.update({"electric_vehicle_v1g", "on_off_ev_charger"})
    if water_heater:
        wanted.add("water_heater")

    controllable = [
        d for d in devices
        if d.get("type") in wanted and "critical_action" in d and "priority" in d
    ]
    return sorted(controllable, key=lambda d: d["priority"])


# ── Status mode ───────────────────────────────────────────────────────────────

def cmd_status(devices: List[Dict[str, Any]]) -> None:
    banner("DEVICE STATUS — CORE API")
    controllable = [d for d in devices if d.get("type") in CONTROLLABLE_TYPES]
    if not controllable:
        warn("No controllable devices found in Core API response.")
        return

    for d in sorted(controllable, key=lambda x: x.get("priority", 99)):
        entity_id = d["entity_id"]
        dev_type = d.get("type", "unknown")
        label = DEVICE_TYPE_LABELS.get(dev_type, dev_type)
        try:
            state = get_device_state(entity_id)
            print(f"\n  {label}")
            print(f"    entity_id      : {entity_id}")
            print(f"    priority       : {d.get('priority')}")
            print(f"    critical_action: {d.get('critical_action')}")
            print(f"    current state  : {state}")
        except Exception as exc:
            warn(f"Could not read state for {entity_id}: {exc}")


# ── Direct setpoint mode ──────────────────────────────────────────────────────

def cmd_direct(
    devices: List[Dict[str, Any]],
    space_heating: bool,
    electric_storage: bool,
    electric_vehicle: bool,
    water_heater: bool,
) -> None:
    """Send critical_action setpoints directly via write_setpoint – same as RTC."""
    banner("DIRECT SETPOINT TEST — using write_setpoint() path")
    info(f"Core API URL : {CORE_API_URL}")
    info("This sends the same POST call that the Real-Time Controller uses.")
    print()

    targets = filter_controllable(devices, space_heating, electric_storage, electric_vehicle, water_heater)
    if not targets:
        warn("No matching controllable devices with critical_action found.")
        return

    results = []
    for d in targets:
        entity_id = d["entity_id"]
        critical_action = d["critical_action"]
        dev_type = d.get("type", "?")
        label = DEVICE_TYPE_LABELS.get(dev_type, dev_type)

        print(f"  {SEP_SMALL}")
        print(f"  {label}  |  {entity_id}")
        print(f"    → Sending setpoint = {critical_action}")

        # Read state before
        try:
            before = get_device_state(entity_id)
            print(f"    State before : {before}")
        except Exception as exc:
            warn(f"Could not read state before: {exc}")
            before = None

        # Send critical action (RTC path)
        try:
            resp = send_setpoint(entity_id, critical_action)
            ok(f"Accepted by Core API — HTTP {resp.status_code}")
            results.append((entity_id, critical_action, "OK"))
        except requests.HTTPError as exc:
            fail(f"HTTP error: {exc.response.status_code} — {exc.response.text[:200]}")
            results.append((entity_id, critical_action, f"HTTP {exc.response.status_code}"))
            continue
        except Exception as exc:
            fail(f"Unexpected error: {exc}")
            results.append((entity_id, critical_action, str(exc)))
            continue

    # Brief wait then re-read states
    print(f"\n  Waiting 4 s for dispatches to propagate to Home Assistant …")
    time.sleep(4)

    print(f"\n{SEPARATOR}")
    print("  POST-COMMAND STATE CHECK")
    print(SEPARATOR)
    for d in targets:
        entity_id = d["entity_id"]
        label = DEVICE_TYPE_LABELS.get(d.get("type", ""), d.get("type", ""))
        try:
            after = get_device_state(entity_id)
            print(f"  {label} [{entity_id}]  state: {after}")
        except Exception as exc:
            warn(f"Could not read state for {entity_id}: {exc}")

    print(f"\n{SEPARATOR}")
    print("  SUMMARY")
    print(SEPARATOR)
    for entity_id, setpoint, result in results:
        status_icon = "✅" if result == "OK" else "❌"
        print(f"  {status_icon}  {entity_id:<30}  setpoint={setpoint:<8}  result={result}")
    print()
    info("Now verify in Home Assistant that the devices received the control actions.")


# ── RTC mode ──────────────────────────────────────────────────────────────────

def cmd_rtc(
    space_heating: bool,
    electric_storage: bool,
    electric_vehicle: bool,
    water_heater: bool,
    duration: int,
) -> None:
    """Run the real RealTimeControl thread with power_limit=0 kW to force curtailment."""
    banner("REAL-TIME CONTROLLER — full production code path")
    info(f"Duration    : {duration} s")
    info(f"Power limit : 0.0 kW  (guarantees curtailment on every cycle)")
    info(f"Devices     : space_heating={space_heating}  battery={electric_storage}  ev={electric_vehicle}  wh={water_heater}")
    print()

    # Build a power_limit dict that spans now → now+duration+some margin
    # All values are 0.0 kW so _needs_curtailment() always returns True
    now = datetime.now().astimezone()
    margin = timedelta(minutes=5)
    end = now + timedelta(seconds=duration) + margin
    interval = timedelta(minutes=1)

    power_limit: Dict[datetime, float] = {}
    ts = now
    while ts <= end:
        power_limit[ts] = 0.0
        ts += interval

    info(f"Power limit horizon: {now.isoformat()} → {end.isoformat()}  ({len(power_limit)} time steps)")
    print()

    # Late import — requires cold_pickup_mpc to be on PYTHONPATH
    try:
        from cold_pickup_mpc.real_time.power_limit_mpc import RealTimeControl
    except ImportError as exc:
        fail(
            f"Cannot import RealTimeControl: {exc}\n"
            "  Make sure you run this script with the predictive-control venv:\n"
            "    uv run python test_real_time_control.py --mode rtc"
        )
        sys.exit(1)

    info("Starting RealTimeControl thread …")
    rtc = RealTimeControl(
        power_limit=power_limit,
        space_heating=space_heating,
        electric_storage=electric_storage,
        electric_vehicle=electric_vehicle,
        water_heater=water_heater,
    )
    rtc.daemon = True  # dies with the main process
    rtc.start()

    try:
        elapsed = 0
        poll_interval = 5
        while elapsed < duration:
            time.sleep(poll_interval)
            elapsed += poll_interval
            running_str = "running ✅" if rtc.is_running else "stopped ❌"
            print(f"  [{elapsed:>3}s / {duration}s]  RTC thread: {running_str}")
            if not rtc.is_alive():
                warn("RTC thread died unexpectedly.")
                break
    except KeyboardInterrupt:
        warn("Interrupted by user.")

    info("Signalling RTC thread to stop …")
    rtc.must_run = False
    rtc.join(timeout=10)

    if rtc.is_alive():
        warn("RTC thread did not stop within 10 s.")
    else:
        ok("RTC thread stopped cleanly.")

    info("Check Home Assistant — all loads should have received their critical_action setpoints.")


# ── Restore mode ──────────────────────────────────────────────────────────────



def cmd_restore(
    devices: List[Dict[str, Any]],
    space_heating: bool,
    electric_storage: bool,
    electric_vehicle: bool,
    water_heater: bool,
) -> None:
    """Send each device's activation_action to restore normal operation.

    Note: ha-device-interface now handles kW -> W conversion for power devices.
    """
    banner("RESTORE — sending activation_action to all devices")
    info("This reverses the curtailment by restoring normal setpoints.")
    print()

    targets = filter_controllable(devices, space_heating, electric_storage, electric_vehicle, water_heater)
    if not targets:
        warn("No matching controllable devices found.")
        return

    for d in targets:
        entity_id = d["entity_id"]
        activation = d.get("activation_action")
        label = DEVICE_TYPE_LABELS.get(d.get("type", ""), d.get("type", ""))

        if activation is None:
            warn(f"{entity_id}: no activation_action defined, skipping.")
            continue

        print(f"  {label}  [{entity_id}]  → activation_action = {activation}")
        try:
            resp = send_setpoint(entity_id, activation)
            ok(f"HTTP {resp.status_code}")
        except Exception as exc:
            fail(str(exc))

    print()
    info("Restore commands sent. Verify normal operation resumes in Home Assistant.")


# ── Entry point ───────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="End-to-end test for the Real-Time Controller (RTC).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--mode",
        choices=["status", "direct", "rtc", "restore"],
        default="status",
        help=(
            "status  : show current device states from Core API\n"
            "direct  : call write_setpoint(critical_action) for all devices\n"
            "rtc     : run the real RealTimeControl thread (power_limit=0)\n"
            "restore : send activation_action to resume normal operation"
        ),
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=60,
        metavar="SECONDS",
        help="Duration (s) to run the RTC thread in --mode rtc (default: 60).",
    )
    # Device type flags
    parser.add_argument("--no-heating", action="store_true", help="Exclude space heating devices.")
    parser.add_argument("--no-battery", action="store_true", help="Exclude battery.")
    parser.add_argument("--no-ev",      action="store_true", help="Exclude electric vehicles.")
    parser.add_argument("--no-wh",      action="store_true", help="Exclude water heater.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    space_heating    = not args.no_heating
    electric_storage = not args.no_battery
    electric_vehicle = not args.no_ev
    water_heater     = not args.no_wh

    banner("REAL-TIME CONTROLLER — END-TO-END TEST")
    info(f"Mode        : {args.mode}")
    info(f"Core API    : {CORE_API_URL}")
    info(f"Timestamp   : {datetime.now().astimezone().isoformat()}")

    # Always verify connectivity first
    print()
    if not check_api_connectivity():
        sys.exit(1)
    ok(f"Core API is reachable at {CORE_API_URL}")

    # For status / direct / restore we need the device list
    if args.mode in ("status", "direct", "restore"):
        try:
            devices = get_devices()
        except Exception as exc:
            fail(f"Could not fetch device list: {exc}")
            sys.exit(1)
        ok(f"Fetched {len(devices)} device(s) from Core API")
    else:
        devices = []

    print()

    if args.mode == "status":
        cmd_status(devices)

    elif args.mode == "direct":
        cmd_direct(devices, space_heating, electric_storage, electric_vehicle, water_heater)

    elif args.mode == "rtc":
        cmd_rtc(space_heating, electric_storage, electric_vehicle, water_heater, args.duration)

    elif args.mode == "restore":
        cmd_restore(devices, space_heating, electric_storage, electric_vehicle, water_heater)


if __name__ == "__main__":
    main()
