import concurrent.futures
from multiprocessing import cpu_count
import random

from flask import Flask, current_app, g, request
import pytest

from flask_executor import Executor
from flask_executor.executor import ExecutorJob, default_workers, WORKERS_MULTIPLIER


# Reusable functions for tests

def fib(n):
    if n <= 2:
        return 1
    else:
        return fib(n-1) + fib(n-2)

def app_context_test_value(_=None):
    return current_app.config['TEST_VALUE']

def request_context_test_value(_=None):
    return request.test_value

def g_context_test_value(_=None):
    return g.test_value


def test_init(app):
    executor = Executor(app)
    assert 'executor' in app.extensions
    assert isinstance(executor, concurrent.futures._base.Executor)
    assert isinstance(executor._executor, concurrent.futures._base.Executor)

def test_factory_init(app):
    executor = Executor()
    executor.init_app(app)
    assert 'executor' in app.extensions
    assert isinstance(executor._executor, concurrent.futures._base.Executor)

def test_thread_executor_init(default_app):
    default_app.config['EXECUTOR_TYPE'] = 'thread'
    executor = Executor(default_app)
    assert isinstance(executor._executor, concurrent.futures.ThreadPoolExecutor)

def test_process_executor_init(default_app):
    default_app.config['EXECUTOR_TYPE'] = 'process'
    executor = Executor(default_app)
    assert isinstance(executor._executor, concurrent.futures.ProcessPoolExecutor)

def test_default_executor_init(default_app):
    executor = Executor(default_app)
    assert isinstance(executor._executor, concurrent.futures.ThreadPoolExecutor)

def test_invalid_executor_init(default_app):
    default_app.config['EXECUTOR_TYPE'] = 'invalid_value'
    try:
        executor = Executor(default_app)
    except ValueError:
        assert True
    else:
        assert False

def test_default_workers(app):
    executor_type = app.config['EXECUTOR_TYPE']
    assert default_workers(executor_type, 2, 6) == None
    assert default_workers(executor_type, 2, 7) == None
    assert default_workers(executor_type, 3, 0) == None
    assert default_workers(executor_type, 3, 1) == None
    assert default_workers(executor_type, 3, 2) == None
    assert default_workers(executor_type, 3, 3) == cpu_count() * WORKERS_MULTIPLIER[executor_type]
    assert default_workers(executor_type, 3, 4) == cpu_count() * WORKERS_MULTIPLIER[executor_type]

def test_submit(app):
    executor = Executor(app)
    future = executor.submit(fib, 5)
    assert future.result() == fib(5)

def test_max_workers(app):
    EXECUTOR_MAX_WORKERS = 10
    app.config['EXECUTOR_MAX_WORKERS'] = EXECUTOR_MAX_WORKERS
    executor = Executor(app)
    assert executor._executor._max_workers == EXECUTOR_MAX_WORKERS

def test_thread_decorator_submit(default_app):
    default_app.config['EXECUTOR_TYPE'] = 'thread'
    executor = Executor(default_app)
    @executor.job
    def decorated(n):
        return fib(n)
    with default_app.test_request_context(''):
        future = decorated.submit(5)
    assert future.result() == fib(5)

def test_thread_decorator_submit_stored(default_app):
    default_app.config['EXECUTOR_TYPE'] = 'thread'
    executor = Executor(default_app)
    @executor.job
    def decorated(n):
        return fib(n)
    with default_app.test_request_context():
        future = decorated.submit_stored('fibonacci', 35)
    assert executor.futures.done('fibonacci') is False
    assert future in executor.futures
    executor.futures.pop('fibonacci')
    assert future not in executor.futures

def test_thread_decorator_map(default_app):
    iterable = list(range(5))
    default_app.config['EXECUTOR_TYPE'] = 'thread'
    executor = Executor(default_app)
    @executor.job
    def decorated(n):
        return fib(n)
    with default_app.test_request_context(''):
        results = decorated.map(iterable)
    for i, r in zip(iterable, results):
        assert fib(i) == r

def test_process_decorator(default_app):
    ''' Using decorators should fail with a TypeError when using the ProcessPoolExecutor '''
    default_app.config['EXECUTOR_TYPE'] = 'process'
    executor = Executor(default_app)
    try:
        @executor.job
        def decorated(n):
            return fib(n)
    except TypeError:
        pass
    else:
        assert 0

def test_submit_app_context(app):
    test_value = random.randint(1, 101)
    app.config['TEST_VALUE'] = test_value
    executor = Executor(app)
    future = executor.submit(app_context_test_value)
    assert future.result() == test_value

def test_submit_g_context_process(app):
    test_value = random.randint(1, 101)
    executor = Executor(app)
    with app.test_request_context(''):
        g.test_value = test_value
        future = executor.submit(g_context_test_value)
    assert future.result() == test_value

def test_submit_request_context(app):
    test_value = random.randint(1, 101)
    executor = Executor(app)
    with app.test_request_context(''):
        request.test_value = test_value
        future = executor.submit(request_context_test_value)
    assert future.result() == test_value

def test_map_app_context(app):
    test_value = random.randint(1, 101)
    iterator = list(range(5))
    app.config['TEST_VALUE'] = test_value
    executor = Executor(app)
    with app.test_request_context(''):
        results = executor.map(app_context_test_value, iterator)
    for r in results:
        assert r == test_value

def test_map_g_context_process(app):
    test_value = random.randint(1, 101)
    iterator = list(range(5))
    executor = Executor(app)
    with app.test_request_context(''):
        g.test_value = test_value
        results = executor.map(g_context_test_value, iterator)
    for r in results:
        assert r == test_value

def test_map_request_context(app):
    test_value = random.randint(1, 101)
    iterator = list(range(5))
    executor = Executor(app)
    with app.test_request_context('/'):
        request.test_value = test_value
        results = executor.map(request_context_test_value, iterator)
    for r in results:
        assert r == test_value

def test_executor_stored_future(default_app):
    executor = Executor(default_app)
    with default_app.test_request_context():
        future = executor.submit_stored('fibonacci', fib, 35)
    assert executor.futures.done('fibonacci') is False
    assert future in executor.futures
    executor.futures.pop('fibonacci')
    assert future not in executor.futures

def test_set_max_futures(default_app):
    default_app.config['EXECUTOR_FUTURES_MAX_LENGTH'] = 10
    executor = Executor(default_app)
    assert executor.futures.max_length == default_app.config['EXECUTOR_FUTURES_MAX_LENGTH']

def test_named_executor(default_app):
    name = 'custom'
    EXECUTOR_MAX_WORKERS = 5
    CUSTOM_EXECUTOR_MAX_WORKERS = 10
    default_app.config['EXECUTOR_MAX_WORKERS'] = EXECUTOR_MAX_WORKERS
    default_app.config['CUSTOM_EXECUTOR_MAX_WORKERS'] = CUSTOM_EXECUTOR_MAX_WORKERS
    executor = Executor(default_app)
    custom_executor = Executor(default_app, name=name)
    assert 'executor' in default_app.extensions
    assert name + 'executor' in default_app.extensions
    assert executor._executor._max_workers == EXECUTOR_MAX_WORKERS
    assert custom_executor._executor._max_workers == CUSTOM_EXECUTOR_MAX_WORKERS

def test_named_executor_submit(app):
    name = 'custom'
    custom_executor = Executor(app, name=name)
    future = custom_executor.submit(fib, 5)
    assert future.result() == fib(5)

def test_named_executor_name(default_app):
    name = 'invalid name'
    try:
        executor = Executor(default_app, name=name)
    except ValueError:
        assert True
    else:
        assert False
