# Predictive Control

[![License](https://img.shields.io/badge/License-LiLiQ_P-blue.svg)](LICENSE.md)
[![Contributing](https://img.shields.io/badge/Contributing-Guidelines-green.svg)](CONTRIBUTING.md)

This repository contains the `predictive_control` Python package, which implements a robust and flexible hybrid control strategy combining Model Predictive Control (MPC) and Real-Time Control (RTC). Designed for intelligent energy management in highly electrified residential homes, this package optimizes energy consumption while ensuring strict adherence to grid limits and user preferences.

This package is a key component within a larger [**Building Intelligence**](https://hq-opensource.github.io/building-intelligence/) ecosystem, consuming data from a central Core API to provide advanced grid services like Cold Load Pickup (CLPU) mitigation and Dynamic Tariff optimization.

---

## Key Features

*   **Hybrid Control Strategy (MPC + RTC):** Proactively plans energy usage with MPC and provides immediate, reactive adjustments with RTC to handle unforeseen consumption spikes.
*   **Flexible Device Integration:** Offers a standardized `DeviceMPC` interface for seamless integration of various controllable devices (e.g., HVAC, water heaters, electric vehicles, batteries).
*   **User-Centric Optimization:** Balances energy cost minimization with occupant comfort by incorporating dynamic pricing and thermal models.

---

## Getting Started

### Prerequisites

*   [Python 3.11+](https://www.python.org/downloads/)
*   [Poetry](https://python-poetry.org/docs/#installation) for dependency management.
*   [Docker](https://docs.docker.com/get-docker/) for containerized execution.

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/hq-opensource/predictive-control.git
    cd predictive-control
    ```

2.  **Install dependencies using Poetry:**
    This command will create a virtual environment and install all the necessary packages defined in `pyproject.toml`.
    ```bash
    poetry install
    ```

---

## Usage

#### Running with Docker

The easiest way to run the application is by using the provided Docker container.

1.  **Build the Docker image:**
    ```bash
    docker build -t predictive-control .
    ```

2.  **Run the Docker container:**
    ```bash
    docker run predictive-control
    ```

#### Running with Poetry

You can also run the application directly using the virtual environment managed by Poetry.

1.  **Activate the virtual environment:**
    ```bash
    poetry shell
    ```

2.  **Run the application:**
    ```bash
    python -m src.cold_pickup_mpc.app
    ```

---

## Contributing
See how to contribute to this project [here](CONTRIBUTING.md).

## License
See the license for this project [here](LICENSE.md).