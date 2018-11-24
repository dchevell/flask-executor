import concurrent.futures
import time

import pytest

from flask_executor import Executor
from flask_executor.futures import FutureCollection, FutureProxy


def fib(n):
    if n <= 2:
        return 1
    else:
        return fib(n-1) + fib(n-2)


def test_plain_future():
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    futures = FutureCollection()
    future = executor.submit(fib, 33)
    futures.add('fibonacci', future)
    assert futures.done('fibonacci') is False
    assert futures._state('fibonacci') is not None
    assert future in futures
    futures.pop('fibonacci')
    assert future not in futures

def test_missing_future():
    futures = FutureCollection()
    assert futures.running('test') is None

def test_duplicate_add_future():
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    futures = FutureCollection()
    future = executor.submit(fib, 33)
    futures.add('fibonacci', future)
    try:
        futures.add('fibonacci', future)
    except ValueError:
        assert True
    else:
        assert False

def test_futures_max_length():
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    futures = FutureCollection(max_length=10)
    future = executor.submit(pow, 2, 4)
    futures.add(0, future)
    assert future in futures
    assert len(futures) == 1
    for i in range(1, 11):
        futures.add(i, executor.submit(pow, 2, 4))
    assert len(futures) == 10
    assert future not in futures

def test_future_proxy(default_app):
    executor = Executor(default_app)
    with default_app.test_request_context(''):
        future = executor.submit(pow, 2, 4)
    # Test if we're returning a subclass of Future
    assert isinstance(future, concurrent.futures.Future)
    assert isinstance(future, FutureProxy)
    concurrent.futures.wait([future])
    # test standard Future methods and attributes
    assert future._state == concurrent.futures._base.FINISHED
    assert future.done()
    assert future.exception(timeout=0) is None

def test_add_done_callback(default_app):
    """Exceptions thrown in callbacks can't be easily caught and make it hard
    to test for callback failure. To combat this, a global variable is used to
    store the value of an exception and test for its existence.
    """
    executor = Executor(default_app)
    global exception
    exception = None
    with default_app.test_request_context(''):
        future = executor.submit(time.sleep, 0.5)
        def callback(future):
            global exception
            try:
                executor.submit(time.sleep, 0)
            except RuntimeError as e:
                exception = e
        future.add_done_callback(callback)
    concurrent.futures.wait([future])
    assert exception is None
