import concurrent.futures

import pytest

from flask_executor.futures import FutureCollection


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

