"""Yices is the top level interface with the yices library."""

import functools

import time

import yices_api as yapi

from .Census import Census
from .Profiler import Profiler


def profile(func):
    """Record the runtime of the decorated function"""
    @functools.wraps(func)
    def wrapper_timer(*args, **kwargs):
        if Profiler.is_enabled():
            start = time.perf_counter_ns()
            value = func(*args, **kwargs)
            stop = time.perf_counter_ns()
            Profiler.delta(func.__name__, start, stop)
            return value
        return func(*args, **kwargs)
    return wrapper_timer


class Yices:
    """A thin wrapper to the yices_api class used for things like profiling."""

    version = yapi.yices_version

    build_arch = yapi.yices_build_arch

    build_mode = yapi.yices_build_mode

    build_date = yapi.yices_build_date

    @staticmethod
    @profile
    def has_mcsat():
        """Return true if the underlying libyices has been compiled with mcsat support, false otherwise."""
        return yapi.yices_has_mcsat() == 1

    @staticmethod
    def is_thread_safe():
        """Return true if the underlying libyices has been compiled with thread safety enabled, false otherwise."""
        return yapi.yices_is_thread_safe() == 1


    # new in 2.6.2
    @staticmethod
    def has_delegate(delegate):
        """Returns True if the underlying libyices has been compiled with the given delegate supported.

        Valid delegates are "cadical", "cryptominisat", and "y2sat".
        """
        return yapi.yices_has_delegate(delegate) == 1

    @staticmethod
    def error_code():
        """Return the last error code, see yices_types.h for a full list."""
        return yapi.yices_error_code()

    @staticmethod
    def error_string():
        """Returns a string explaining the last error."""
        return yapi.yices_error_string()

    @staticmethod
    def error_report():
        """Return the latest error report, see yices.h."""
        return yapi.yices_error_report()

    @staticmethod
    def clear_error():
        """Clears the error reprt structure."""
        return yapi.yices_clear_error()

    @staticmethod
    def print_error(fd):
        """Prints the error report out to the given file descriptor."""
        return yapi.yices_print_error_fd(fd)

    @staticmethod
    def init():
        """Must be called before any other API routine (other than is_inited), to initialize internal data structures."""
        yapi.yices_init()

    @staticmethod
    def is_inited():
        """Return True if the library has been initialized, False otherwise."""
        return yapi.yices_is_inited()

    @staticmethod
    def exit(census=False):
        """Deletes all the internal data structure, must be called on exiting to prevent leaks."""
        if census:
            print(Census.dump())
            print(Profiler.dump())
        yapi.yices_exit()

    @staticmethod
    def reset():
        """Resets all the internal data structures."""
        yapi.yices_reset()


    #################
    #   CONTEXTS    #
    #################

    @staticmethod
    @profile
    def new_context(config):
        """Returns a newly allocated context; a context is a stack of assertions."""
        return yapi.yices_new_context(config)

    @staticmethod
    @profile
    def free_context(ctx):
        """Frees the given context."""
        yapi.yices_free_context(ctx)

    @staticmethod
    @profile
    def context_status(ctx):
        """The context status."""
        return yapi.yices_context_status(ctx)

    @staticmethod
    @profile
    def reset_context(ctx):
        """Removes all assertions from the context."""
        yapi.yices_reset_context(ctx)

    @staticmethod
    @profile
    def push(ctx):
        """Marks a backtrack point in the context."""
        return yapi.yices_push(ctx)

    @staticmethod
    @profile
    def pop(ctx):
        """Backtracks to the previous backtrack point."""
        return yapi.yices_pop(ctx)
