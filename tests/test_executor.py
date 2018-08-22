import concurrent.futures

from flask import Flask
from flask_executor import Executor, ExecutorJob
import pytest


EXECUTOR_MAX_WORKERS = 10

def fib(n):
    if n <= 2:
        return 1
    else:
        return fib(n-1) + fib(n-2)


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
        assert type(executor._executor) == concurrent.futures.ThreadPoolExecutor

def test_thread_executor(app):
    app.config['EXECUTOR_TYPE'] = 'thread'
    executor = Executor(app)
    with app.app_context():
        executor.submit(fib, 5)
        assert type(executor._executor) == concurrent.futures.ThreadPoolExecutor

def test_process_executor(app):
    app.config['EXECUTOR_TYPE'] = 'process'
    executor = Executor(app)
    with app.app_context():
        executor.submit(fib, 5)
        assert type(executor._executor) == concurrent.futures.ProcessPoolExecutor

def test_submit_result(app):
    executor = Executor(app)
    with app.app_context():
        future = executor.submit(fib, 5)
        assert type(future) == concurrent.futures.Future
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
    assert type(decorated) == ExecutorJob
    with app.app_context():
        future = decorated.submit(5)
        assert type(future) == concurrent.futures.Future
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

