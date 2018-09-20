import concurrent.futures
import random

from flask import Flask, current_app, g, request
import pytest

from flask_executor import Executor, ExecutorJob


EXECUTOR_MAX_WORKERS = 10


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


# Begin tests

def test_init(app):
    executor = Executor(app)
    assert 'executor' in app.extensions

def test_factory_init(app):
    executor = Executor()
    executor.init_app(app)
    assert 'executor' in app.extensions

def test_default_executor(app):
    executor = Executor(app)
    with app.app_context():
        executor.submit(fib, 5)
        assert isinstance(executor._executor, concurrent.futures.ThreadPoolExecutor)

def test_thread_executor(app):
    app.config['EXECUTOR_TYPE'] = 'thread'
    executor = Executor(app)
    with app.app_context():
        executor.submit(fib, 5)
        assert isinstance(executor._executor, concurrent.futures.ThreadPoolExecutor)

def test_process_executor(app):
    app.config['EXECUTOR_TYPE'] = 'process'
    executor = Executor(app)
    with app.app_context():
        executor.submit(fib, 5)
        assert isinstance(executor._executor, concurrent.futures.ProcessPoolExecutor)

def test_submit_result(app):
    executor = Executor(app)
    with app.app_context():
        future = executor.submit(fib, 5)
        assert isinstance(future, concurrent.futures.Future)
        assert future.result() == fib(5)

def test_thread_workers(app):
    app.config['EXECUTOR_TYPE'] = 'thread'
    app.config['EXECUTOR_MAX_WORKERS'] = EXECUTOR_MAX_WORKERS
    executor = Executor(app)
    with app.app_context():
        executor.submit(fib, 5)
        assert executor._executor._max_workers == EXECUTOR_MAX_WORKERS

def test_process_workers(app):
    app.config['EXECUTOR_TYPE'] = 'process'
    app.config['EXECUTOR_MAX_WORKERS'] = EXECUTOR_MAX_WORKERS
    executor = Executor(app)
    with app.app_context():
        executor.submit(fib, 5)
        assert executor._executor._max_workers == EXECUTOR_MAX_WORKERS

def test_thread_decorator(app):
    app.config['EXECUTOR_TYPE'] = 'thread'
    executor = Executor(app)
    @executor.job
    def decorated(n):
        return fib(n)
    assert isinstance(decorated, ExecutorJob)
    with app.app_context():
        future = decorated.submit(5)
        assert isinstance(future, concurrent.futures.Future)
        assert future.result() == fib(5)

def test_process_decorator(app):
    ''' Using decorators should fail with a TypeError when using the ProcessPoolExecutor '''
    app.config['EXECUTOR_TYPE'] = 'process'
    executor = Executor(app)
    try:
        @executor.job
        def decorated(n):
            return fib(n)
    except TypeError:
        pass
    else:
        assert 0

def test_app_context_thread(app):
    test_value = random.randint(1, 101)
    app.config['EXECUTOR_TYPE'] = 'thread'
    app.config['TEST_VALUE'] = test_value
    executor = Executor(app)
    future = executor.submit(app_context_test_value)
    assert future.result() == test_value

def test_request_context_thread(app):
    test_value = random.randint(1, 101)
    app.config['EXECUTOR_TYPE'] = 'thread'
    executor = Executor(app)
    with app.test_request_context('/'):
        request.test_value = test_value
        future = executor.submit(request_context_test_value)
    assert future.result() == test_value

def test_g_context_thread(app):
    test_value = random.randint(1, 101)
    app.config['EXECUTOR_TYPE'] = 'thread'
    executor = Executor(app)
    with app.test_request_context(''):
        g.test_value = test_value
        future = executor.submit(g_context_test_value)
    assert future.result() == test_value

def test_app_context_process(app):
    test_value = random.randint(1, 101)
    app.config['EXECUTOR_TYPE'] = 'process'
    app.config['TEST_VALUE'] = test_value
    executor = Executor(app)
    future = executor.submit(app_context_test_value)
    assert future.result() == test_value

def test_request_context_process(app):
    test_value = random.randint(1, 101)
    app.config['EXECUTOR_TYPE'] = 'process'
    executor = Executor(app)
    with app.test_request_context(''):
        request.test_value = test_value
        future = executor.submit(request_context_test_value)
    assert future.result() == test_value

def test_g_context_process(app):
    test_value = random.randint(1, 101)
    app.config['EXECUTOR_TYPE'] = 'process'
    executor = Executor(app)
    with app.test_request_context(''):
        g.test_value = test_value
        future = executor.submit(g_context_test_value)
    assert future.result() == test_value

def test_map_thread(app):
    iterable = list(range(1, 6))
    app.config['EXECUTOR_TYPE'] = 'thread'
    executor = Executor(app)
    results = executor.map(fib, iterable)
    for i, r in zip(iterable, results):
        assert fib(i) == r

def test_map_process(app):
    iterable = list(range(1, 6))
    app.config['EXECUTOR_TYPE'] = 'process'
    executor = Executor(app)
    results = executor.map(fib, iterable)
    for i, r in zip(iterable, results):
        assert fib(i) == r

def test_map_app_context(app):
    test_value = random.randint(1, 101)
    iterator = list(range(5))
    app.config['TEST_VALUE'] = test_value
    executor = Executor(app)
    results = executor.map(app_context_test_value, iterator)
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

def test_map_g_context(app):
    test_value = random.randint(1, 101)
    iterator = list(range(5))
    executor = Executor(app)
    with app.test_request_context(''):
        g.test_value = test_value
        results = executor.map(g_context_test_value, iterator)
    for r in results:
        assert r == test_value

def test_map_decorator(app):
    iterable = list(range(5))
    executor = Executor(app)
    @executor.job
    def decorated(n):
        return fib(n)
    results = decorated.map(iterable)
    for i, r in zip(iterable, results):
        assert fib(i) == r
