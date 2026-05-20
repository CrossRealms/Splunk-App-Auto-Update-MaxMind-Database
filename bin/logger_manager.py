# This file is generated and maintained by splunk-app-action (https://github.com/VatsalJagani/splunk-app-action)
# To modify anything create Pull Request on the splunk-app-action GitHub repository.


# Standard library imports
import logging
import logging.handlers
import os
from typing import cast

# Splunk imports
from splunk.clilib.bundle_paths import make_splunkhome_path

log_file_prefix: str = "auto_update_maxmind_db"


def setup_logging(log_name: str, log_level: int = logging.INFO) -> logging.Logger:
    """Setup logger.

    :param log_name: name for logger
    :param log_level: log level, a string
    :return: a logger object
    """
    log_name = f"{log_file_prefix}_{log_name}"
    # Make path till log file (current dir (app/<app-name>/bin))
    # log_dir = os.path.dirname(os.path.abspath(__file__))
    # log_file = os.path.join(log_dir, "%s.log" % log_name)

    # Make path till log file (splunk/var/log/splunk dir)
    log_file_path = make_splunkhome_path(["var", "log", "splunk", f"{log_name}.log"])
    log_file: str = str(log_file_path) if log_file_path is not None else f"./logs/{log_name}.log"
    log_dir: str = os.path.dirname(log_file)

    # Create directory at the required path to store log file, if not found
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = logging.getLogger(log_name)
    logger.propagate = False

    # Set log level
    logger.setLevel(log_level)

    handler_exists = any(
        [
            True
            for h in logger.handlers
            if hasattr(h, "baseFilename")
            and cast(logging.handlers.RotatingFileHandler, h).baseFilename == log_file
        ]
    )

    if not handler_exists:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, mode="a", maxBytes=10485760, backupCount=10
        )
        # Format logs
        fmt_str = "%(asctime)s %(levelname)s %(thread)d - %(message)s"
        formatter = logging.Formatter(fmt_str, datefmt="%Y-%m-%d %H:%M:%S %z")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        file_handler.setLevel(log_level)

    return logger
