"""This package contains modules responsible for the core Model Predictive Control (MPC) logic.

It encompasses the entire MPC workflow, from building the global optimization
problem to executing the solver, interpreting the results, and scheduling
control actions.

The key modules within this package include:
- `build_mpc.py`: Defines the `BuildGlobalMPC` class, which aggregates individual
  device MPC formulations into a single, comprehensive optimization problem,
  incorporating global constraints like electricity prices and power limits.
- `executor.py`: Defines the `ExecutorMPC` class, which orchestrates the MPC
  process by initializing the problem builder, running the optimization, and
  returning the solved problem.
- `interpreter.py`: Defines the `Interpreter` class, responsible for extracting
  and processing optimal variable values from the solved MPC problem, transforming
  them into meaningful data structures, and persisting results to a database.
- `rpc.py`: Handles Remote Procedure Call (RPC) communication for the MPC system,
  setting up a Redis-based message broker to listen for and process incoming
  MPC requests, scheduling the main MPC and real-time control jobs.
- `schedule.py`: Provides utilities for posting the generated control schedules
  to the Core API, translating the MPC's calculated dispatch decisions into
  actionable commands for connected devices.

Together, these modules form the brain of the Cold Pickup MPC system, enabling
it to make intelligent energy management decisions.
"""
