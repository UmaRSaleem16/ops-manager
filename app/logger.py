"""
Logger

General purpose logging module.  All logs will come through as info when function logger.Log() is used,
if you would like to add different logging levels to your module import logging and
use logger.Log('message', logging.ERROR) format.

This also handles file rotation and caps the size of the log file.  Both as globals that can be set.
"""

__author__ = 'Sunrise Cobb <scobb@guardiananalytics.com>'

import os
import logging
import traceback
import logging.handlers

# python 2 vs 3
from app import utility

# import commander.utility as utility


# set log file params
DEFAULT_NAME = 'app/manager'
LOG_FILENAME = '%s.log' % DEFAULT_NAME
MAX_BYTES = 1024 * 1024 * 10  # 10MB files
BACKUP_COUNT = 5


def SetupLogger(path, max_bytes=MAX_BYTES, backup_count=BACKUP_COUNT):
    """
    Setup for our log management.

    Args: path(string), max_bytes(int), backup_count(int)

    Returns: None
    """

    global DEFAULT_NAME, LOG_FILENAME, MAX_BYTES, BACKUP_COUNT

    name = os.path.splitext(os.path.basename(path))[0]

    DEFAULT_NAME = name
    LOG_FILENAME = path
    MAX_BYTES = max_bytes
    BACKUP_COUNT = backup_count


def GetLogger(stdout=False):
    """
    Sets up logging.  Will output to logfile and stdout if True

    Args: stdout(boolean)

    Returns: LOGGER(string)
    """

    if not utility.LOGGER:

        # NOTE(sunrise): Original ops logging format
        # format = '%(asctime)-15s %(levelname)-8s %(trace)-5s %(message)s'

        format = '%(asctime)s  %(levelname)s  %(message)s (%(trace)-5s)'

        utility.LOGGER = logging.getLogger(DEFAULT_NAME)
        utility.LOGGER.setLevel(utility.LOG_LEVEL)

        # OK so... this is ghetto we do it cause otherwise the getLogger dupes log lines
        # https://stackoverflow.com/questions/7173033/duplicate-log-output-when-using-python-logging-module
        try:
            if file_handler:
                file_handler.setLevel(utility.LOG_LEVEL)
        except:
            pass

        if not utility.LOGGER.handlers:

            # NOTE(sunrise): This cannot be assigned to the LOGGER object, or it will ignore the handlers and not log
            formatter = logging.Formatter(format)

            # rotating file
            # file_handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT)

            # NOTE(sunrise): modded for MCUI-2593
            file_handler = logging.handlers.TimedRotatingFileHandler(LOG_FILENAME, when="d", interval=1,
                                                                     backupCount=BACKUP_COUNT)
            file_handler.setFormatter(formatter)
            utility.LOGGER.addHandler(file_handler)

            # NOTE(sunrise): This is the stream handler for outputting to STDOUT
            if stdout:
                stream_handler = logging.StreamHandler()
                stream_handler.setLevel(utility.LOG_LEVEL)
                stream_handler.setFormatter(formatter)
                utility.LOGGER.addHandler(stream_handler)

    return utility.LOGGER


def Log(text, level=logging.INFO, stack=0):
    """
    Outputs our desired log format.

    Args: text(string), level(string), stack(int)

    Returns: None
    """

    logger = GetLogger()

    stack_list = traceback.extract_stack()
    (module_name, line_number) = stack_list[-2][:2]
    # module_name = os.path.splitext(module_name)[0]
    module_name = os.path.splitext(os.path.basename(module_name))[0]

    # Get the mini stack!
    if stack > 0:
        mini_stack_list = stack_list[-(stack + 1):-1]

        mini_text = ''
        for mini_stack in mini_stack_list:
            if mini_text:
                mini_text += ' -> '

            (stack_name, stack_line_number) = mini_stack[:2]
            stack_name = os.path.splitext(os.path.basename(stack_name))[0]
            mini_text += '%s:%s' % (stack_name, stack_line_number)

        # Add the mini_text to our text, so we see the mini-stack trace
        text += ' (%s)' % mini_text

    logger.log(level, text, extra={'trace': '%s:%s' % (module_name, line_number)})


