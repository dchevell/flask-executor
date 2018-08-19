import concurrent.futures

from flask import Flask
from flask_executor import Executor
import pytest


def fib(n):
    if n <= 2:
        return 1
    else:
        return fib(n-1) + fib(n-2)


def test_init():
    app = Flask(__name__)
    executor = Executor(app)
    assert 'executor' in app.extensions

def test_factory_init():
    app = Flask(__name__)
    executor = Executor()
    executor.init_app(app)
    assert 'executor' in app.extensions

def test_default_executor():
    app = Flask(__name__)
    executor = Executor(app)
    with app.app_context():
        executor.submit(fib, 5)
        assert type(executor._executor) == concurrent.futures.ThreadPoolExecutor

def test_thread_executor():
    app = Flask(__name__)
    app.config['EXECUTOR_TYPE'] = 'thread'
    executor = Executor(app)
    with app.app_context():
        executor.submit(fib, 5)
        assert type(executor._executor) == concurrent.futures.ThreadPoolExecutor

def test_process_executor():
    app = Flask(__name__)
    app.config['EXECUTOR_TYPE'] = 'process'
    executor = Executor(app)
    with app.app_context():
        executor.submit(fib, 5)
        assert type(executor._executor) == concurrent.futures.ProcessPoolExecutor

def test_submit_result():
    app = Flask(__name__)
    executor = Executor(app)
    with app.app_context():
        future = executor.submit(fib, 5)
        assert type(future) == concurrent.futures.Future
        assert future.result() == fib(5)

def test_thread_workers():
    MAX_WORKERS = 10
    app = Flask(__name__)
    app.config['EXECUTOR_TYPE'] = 'thread'
    app.config['EXECUTOR_MAX_WORKERS'] = MAX_WORKERS
    executor = Executor(app)
    with app.app_context():
        executor.submit(fib, 5)
        assert executor._executor._max_workers == MAX_WORKERS

def test_process_workers():
    MAX_WORKERS = 10
    app = Flask(__name__)
    app.config['EXECUTOR_TYPE'] = 'process'
    app.config['EXECUTOR_MAX_WORKERS'] = MAX_WORKERS
    executor = Executor(app)
    with app.app_context():
        executor.submit(fib, 5)
        assert executor._executor._max_workers == MAX_WORKERS
