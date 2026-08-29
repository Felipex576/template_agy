"""" This module contains the decorators used in the project. """

import functools

from src.config.logger import logger

def log_decorator(func):
    """ A decorator that logs the start of the execution of the decorated function. """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        """ Wrapper function that logs the start of the execution of the decorated function. """
        logger.info(f"# [INFO]: Start {func.__name__}")
        return func(*args, **kwargs)
    return wrapper

def raise_decorator(func):
    """
    A decorator that wraps a function to provide a general-purpose exception handler.
    This decorator logs any exceptions raised by the decorated function and then re-raises the exception.
    """
    def wrapper(*args, **kwargs):
        """ A general-purpose exception handler decorator. """
        try:
            return func(*args, **kwargs)
        except Exception as err:
            msg_error = str(err)
            logger.error(f"# [ERROR]: En funcion {func.__name__}: {msg_error}")
            raise err
    return wrapper