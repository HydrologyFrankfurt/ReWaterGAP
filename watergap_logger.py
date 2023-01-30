# -*- coding: utf-8 -*-
"""Logger Function."""
import logging
import datetime


# ===============================================================
# Setting up logger
# ===============================================================


def config_logger(level, modname, msg, debug=False):
    """
    Set logger.

    Parameters
    ----------
    modname : str
        Module name
    level : logging level
        Set level as e.g. logging.DEBUG.
        Prefix of  level should always be
        'logging.(level name)'
    debug : bool(True or False)
        Optional argument to enable or disable traceback for debugging

    Returns
    -------
    logger :
        returns logging information.

    """
    # assign True or False to debug
    logdate = datetime.datetime.now()
    logdate = logdate.strftime("%Y-%m-%d-%H-%M-%S")
    logger = logging.getLogger(modname)

    # Checking for existing logging handlers else multiple log statement will
    # be printed to the same log file
    formatter = logging.Formatter('%(asctime)s:%(name)s:%(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
    file_handler = logging.FileHandler(modname+'_'+logdate+".log")
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    # exc_info produes full traceback of error
    if level == logging.ERROR:
        logger.setLevel(level)
        logger.error(msg, exc_info=debug)
        file_handler.close()  # close log after writing
        logger.handlers.clear()
    elif level == logging.CRITICAL:
        logger.setLevel(level)
        logger.critical(msg, exc_info=debug)
        file_handler.close()
        logger.handlers.clear()
    elif level == logging.WARNING:
        logger.setLevel(level)
        logger.warning(msg, exc_info=False)
        file_handler.close()
        logger.handlers.clear()
    elif level == logging.INFO:
        logger.setLevel(level)
        logger.info(msg, exc_info=False)
        file_handler.close()
        logger.handlers.clear()
    elif level == logging.DEBUG:
        logger.setLevel(level)
        logger.debug(msg, exc_info=debug)
        file_handler.close()
        logger.handlers.clear()
    else:
        raise ValueError('Wrong logging level. Please enter a correct'
                         ' level. Should be words or numeric. see '
                         'https://docs.python.org/'
                         '3/library/logging.html#levels')

    return logger
