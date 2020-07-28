import asyncio
import functools


def async_test(f):
    """
    A wrapper for asynchronous tests.
    By default unittest will not wait for asynchronous tests to complete even if the async functions are awaited.
    By annotating a test method with `@async_test` it will cause the test to wait for asynchronous activities
    to complete
    :param f:
    :return:
    """
    functools.wraps(f)

    def wrapper(*args, **kwargs):
        coro = asyncio.coroutine(f)
        future = coro(*args, **kwargs)
        asyncio.run(future)

    return wrapper


def awaitable(result=None):
    """
    Create a :class:`asyncio.Future` that is completed and returns result.
    :param result: to return
    :return: a completed :class:`asyncio.Future`
    """
    future = asyncio.Future()
    future.set_result(result)
    return future


def awaitable_exception(exception: Exception):
    """
    Create a :class:`asyncio.Future` that is completed and raises an exception.
    :param exception: to raise
    :return: a completed :class:`asyncio.Future`
    """
    future = asyncio.Future()
    future.set_exception(exception)
    return future
