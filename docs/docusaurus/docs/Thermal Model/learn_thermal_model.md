---
sidebar_position: 1
---

# Learn Thermal Model

This module defines the `LearnThermalDynamics` class, which manages the learning, validation, and persistence of thermal models for space heating.

This class is responsible for:
- Retrieving historical data (indoor temperature, heater consumption, weather) from the Core API.
- Preprocessing this data for use in a thermal model learning algorithm.
- Executing the learning process to derive a state-space thermal model.
- Validating if an existing thermal model is up-to-date or if re-learning is required.
- Saving and loading learned thermal models to/from a JSON file for persistence.
- Providing a default thermal model if learning fails or insufficient data is available.

## Classes

### `LearnThermalDynamics`

Manages the learning, validation, and persistence of thermal models for space heating.

#### Methods

##### `__init__()`

Initializes the `LearnThermalDynamics` by retrieving information about all devices.

##### `validate_or_learn_model(start: datetime, stop: datetime) -> Dict[str, Any]`

Validates if a thermal model exists and is recent; otherwise, it learns a new one.

This method checks for a saved thermal model. If found, it verifies if the model was learned within a `learning_threshold` (e.g., 1 day). If the model is missing, outdated, or cannot be loaded, it triggers the `execute_learning` process.

**Args:**

- `start`: The start datetime for retrieving historical data if learning is needed.
- `stop`: The stop datetime for retrieving historical data if learning is needed.

**Returns:**

- A dictionary containing the validated, newly learned, or default thermal model.

##### `execute_learning(start: datetime, stop: datetime, old_model_exists: bool = True) -> Dict[str, Any]`

Executes the learning process for the thermal models.

This method retrieves historical data, processes it, and then attempts to learn a black-box thermal model using the `ThermalModels` class. If learning fails (e.g., due to insufficient data or optimization issues), it provides either an existing old model or a default model.

**Args:**

- `start`: The start datetime for retrieving historical data.
- `stop`: The stop datetime for retrieving historical data.
- `old_model_exists`: A boolean indicating if an old model was found, used for logging purposes.

**Returns:**

- A dictionary containing the learned thermal model parameters (Ax, Au, Aw) and metadata, or a default model if learning is unsuccessful.