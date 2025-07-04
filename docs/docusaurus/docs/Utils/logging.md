---
sidebar_position: 1
---

# Logging

This module provides a centralized utility for configuring and managing application logging.

It defines the `LoggingUtil` class, which offers a static method to retrieve pre-configured logger instances. This ensures consistent logging practices across the entire application, allowing for standardized log formats and dynamic adjustment of log levels via environment variables.

## Classes

### `LoggingUtil`

A utility class for configuring and retrieving loggers.

This class provides a static method to get a pre-configured logger instance, ensuring consistent logging format and level across the application. The log level can be controlled via an environment variable.

#### Methods

##### `get_logger(logger_name: str) -> logging.Logger`

Retrieves a configured logger instance.

The logger's level is determined by the 'LOGLEVEL' environment variable. If 'LOGLEVEL' is not set or is invalid, it defaults to INFO. The logger outputs messages to the console with a standardized format.

**Args:**

- `logger_name`: The name of the logger to retrieve (typically `__name__` of the calling module).

**Returns:**

- A configured `logging.Logger` instance.