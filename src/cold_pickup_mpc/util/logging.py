import logging
import os


class LoggingUtil:
    @staticmethod
    def get_logger(logger_name: str) -> logging.Logger:
        logger = logging.getLogger(logger_name)
        log_level = os.getenv("LOGLEVEL", logging.INFO)

        if log_level not in logging._nameToLevel.keys():
            log_level = logging.INFO

        logger.setLevel(log_level)

        log_formatter = logging.Formatter("%(asctime)s - [%(name)s][%(levelname)s] %(message)s")

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_formatter)
        logger.addHandler(console_handler)

        return logger
