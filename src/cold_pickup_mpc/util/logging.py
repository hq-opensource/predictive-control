"""This module provides a centralized utility for configuring and managing application logging.

It defines the `LoggingUtil` class, which offers a static method to retrieve
pre-configured logger instances. This ensures consistent logging practices
across the entire application, allowing for standardized log formats and
dynamic adjustment of log levels via environment variables.
"""

import logging
import os


class LoggingUtil:
    """A utility class for configuring and retrieving loggers.

    This class provides a static method to get a pre-configured logger
    instance, ensuring consistent logging format and level across the application.
    The log level can be controlled via an environment variable.
    """

    @staticmethod
    def get_logger(logger_name: str) -> logging.Logger:
        """Retrieves a configured logger instance.

        The logger's level is determined by the 'LOGLEVEL' environment variable.
        If 'LOGLEVEL' is not set or is invalid, it defaults to INFO.
        The logger outputs messages to the console with a standardized format.

        Args:
            logger_name: The name of the logger to retrieve (typically `__name__`
                         of the calling module).

        Returns:
            A configured `logging.Logger` instance.
        """
        logger = logging.getLogger(logger_name)
        log_level = os.getenv("LOGLEVEL", logging.INFO)

        if log_level not in logging._nameToLevel.keys():
            log_level = logging.INFO

        logger.setLevel(log_level)

        log_formatter = logging.Formatter(
            "%(asctime)s - [%(name)s][%(levelname)s] %(message)s"
        )

        # Ensure that handlers are not duplicated if get_logger is called multiple times
        if not logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(log_formatter)
            logger.addHandler(console_handler)

        return logger
