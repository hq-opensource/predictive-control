---
sidebar_position: 4
---

# RPC

This module handles the Remote Procedure Call (RPC) communication for the MPC system.

It sets up a Redis-based message broker using FastStream to listen for incoming MPC requests. The `handle_mpc_request` asynchronous function processes these requests, extracts relevant parameters, and then schedules the main MPC optimization and real-time control jobs. This module acts as the entry point for external systems to trigger MPC runs.

## Functions

### `handle_mpc_request(mpc_request: Dict[str, Any]) -> bool`

Handles incoming MPC requests via Redis RPC.

This asynchronous function acts as a subscriber to the 'mpc' topic. It receives MPC parameters, validates them, and then schedules the main MPC and control jobs. If no parameters are provided, it interprets this as a signal to stop the real-time control job.

**Args:**

- `mpc_request`: A dictionary containing the MPC request, expected to have a 'params' key with detailed optimization parameters.

**Returns:**

- `True` if the MPC and control jobs are successfully scheduled, `False` otherwise.