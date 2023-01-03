import concurrent
import concurrent.futures
import logging
import random
import time
from concurrent.futures import _base
from threading import local

import pytest
from flask import current_app, g, request

from flask_executor import Executor
from flask_executor.executor import propagate_exceptions_callback


# Reusable functions for tests

def fib(n):
    if n <= 2:
        return 1
    else:
        return fib(n - 1) + fib(n - 2)


def app_context_test_value(_=None):
    return current_app.config['TEST_VALUE']


def request_context_test_value(_=None):
    return request.test_value


def g_context_test_value(_=None):
    return g.test_value


def fail():
    time.sleep(0.1)
    print(hello)


class CustomThreadPoolExecutor(concurrent.futures.ThreadPoolExecutor):
    class _Future(_base.Future):
        def __getattr__(self, item):
            return lambda: True

    def submit(self, fn, *args, **kwargs):
        return self._Future()


def test_init(app):
    executor = Executor(app)
    assert 'executor' in app.extensions
    assert isinstance(executor, concurrent.futures._base.Executor)
    assert isinstance(executor._self, concurrent.futures._base.Executor)
    assert getattr(executor, 'shutdown')


def test_factory_init(app):
    executor = Executor()
    executor.init_app(app)
    assert 'executor' in app.extensions
    assert isinstance(executor._self, concurrent.futures._base.Executor)


def test_thread_executor_init(default_app):
    default_app.config['EXECUTOR_TYPE'] = 'thread'
    executor = Executor(default_app)
    assert isinstance(executor._self, concurrent.futures.ThreadPoolExecutor)
    assert isinstance(executor, concurrent.futures.ThreadPoolExecutor)


def test_process_executor_init(default_app):
    default_app.config['EXECUTOR_TYPE'] = 'process'
    executor = Executor(default_app)
    assert isinstance(executor._self, concurrent.futures.ProcessPoolExecutor)
    assert isinstance(executor, concurrent.futures.ProcessPoolExecutor)


def test_custom_executor_init(default_app):
    default_app.config['EXECUTOR_TYPE'] = 'custom'
    default_app.config['EXECUTOR_POOL_CLASS'] = CustomThreadPoolExecutor
    executor = Executor(default_app)
    assert isinstance(executor._self, CustomThreadPoolExecutor)
    assert isinstance(executor, CustomThreadPoolExecutor)


def test_invalid_process_custom_init(default_app):
    default_app.config['EXECUTOR_TYPE'] = 'custom'
    with pytest.raises(ValueError):
        _ = Executor(default_app)


def test_default_executor_init(default_app):
    executor = Executor(default_app)
    assert isinstance(executor._self, concurrent.futures.ThreadPoolExecutor)


def test_invalid_executor_init(default_app):
    default_app.config['EXECUTOR_TYPE'] = 'invalid_value'
    try:
        executor = Executor(default_app)
    except ValueError:
        assert True
    else:
        assert False


def test_submit(app):
    executor = Executor(app)
    with app.test_request_context(''):
        future = executor.submit(fib, 5)
    assert future.result() == fib(5)


def test_max_workers(app):
    EXECUTOR_MAX_WORKERS = 10
    app.config['EXECUTOR_MAX_WORKERS'] = EXECUTOR_MAX_WORKERS
    executor = Executor(app)
    assert executor._max_workers == EXECUTOR_MAX_WORKERS
    assert executor._self._max_workers == EXECUTOR_MAX_WORKERS


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


def test_submit_app_context(default_app):
    test_value = random.randint(1, 101)
    default_app.config['TEST_VALUE'] = test_value
    executor = Executor(default_app)
    with default_app.test_request_context(''):
        future = executor.submit(app_context_test_value)
    assert future.result() == test_value


def test_submit_g_context_process(default_app):
    test_value = random.randint(1, 101)
    executor = Executor(default_app)
    with default_app.test_request_context(''):
        g.test_value = test_value
        future = executor.submit(g_context_test_value)
    assert future.result() == test_value


def test_submit_request_context(default_app):
    test_value = random.randint(1, 101)
    executor = Executor(default_app)
    with default_app.test_request_context(''):
        request.test_value = test_value
        future = executor.submit(request_context_test_value)
    assert future.result() == test_value


def test_map_app_context(default_app):
    test_value = random.randint(1, 101)
    iterator = list(range(5))
    default_app.config['TEST_VALUE'] = test_value
    executor = Executor(default_app)
    with default_app.test_request_context(''):
        results = executor.map(app_context_test_value, iterator)
    for r in results:
        assert r == test_value


def test_map_g_context_process(default_app):
    test_value = random.randint(1, 101)
    iterator = list(range(5))
    executor = Executor(default_app)
    with default_app.test_request_context(''):
        g.test_value = test_value
        results = executor.map(g_context_test_value, iterator)
    for r in results:
        assert r == test_value


def test_map_request_context(default_app):
    test_value = random.randint(1, 101)
    iterator = list(range(5))
    executor = Executor(default_app)
    with default_app.test_request_context('/'):
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
    assert executor._self._max_workers == EXECUTOR_MAX_WORKERS
    assert executor._max_workers == EXECUTOR_MAX_WORKERS
    assert custom_executor._self._max_workers == CUSTOM_EXECUTOR_MAX_WORKERS
    assert custom_executor._max_workers == CUSTOM_EXECUTOR_MAX_WORKERS


def test_named_executor_submit(app):
    name = 'custom'
    custom_executor = Executor(app, name=name)
    with app.test_request_context(''):
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


def test_default_done_callback(app):
    executor = Executor(app)

    def callback(future):
        setattr(future, 'test', 'test')

    executor.add_default_done_callback(callback)
    with app.test_request_context('/'):
        future = executor.submit(fib, 5)
        concurrent.futures.wait([future])
        assert hasattr(future, 'test')


def test_propagate_exception_callback(app, caplog):
    caplog.set_level(logging.ERROR)
    app.config['EXECUTOR_PROPAGATE_EXCEPTIONS'] = True
    executor = Executor(app)
    with pytest.raises(NameError):
        with app.test_request_context('/'):
            future = executor.submit(fail)
            concurrent.futures.wait([future])
            future.result()


def test_coerce_config_types(default_app):
    default_app.config['EXECUTOR_MAX_WORKERS'] = '5'
    default_app.config['EXECUTOR_FUTURES_MAX_LENGTH'] = '10'
    default_app.config['EXECUTOR_PROPAGATE_EXCEPTIONS'] = 'true'
    executor = Executor(default_app)
    with default_app.test_request_context():
        future = executor.submit_stored('fibonacci', fib, 35)


def test_shutdown_executor(default_app):
    executor = Executor(default_app)
    assert executor._shutdown is False
    executor.shutdown()
    assert executor._shutdown is True


def test_pre_init_executor(default_app):
    executor = Executor()

    @executor.job
    def decorated(n):
        return fib(n)

    assert executor
    executor.init_app(default_app)
    with default_app.test_request_context(''):
        future = decorated.submit(5)
    assert future.result() == fib(5)


def test_custom_executor_getarrt(default_app):
    default_app.config['EXECUTOR_TYPE'] = 'custom'
    default_app.config['EXECUTOR_POOL_CLASS'] = CustomThreadPoolExecutor
    executor = Executor(default_app)
    with default_app.test_request_context(''):
        executor.submit_stored('fibonacci', fib, 35)
    assert executor.futures.custom_func('fibonacci')


thread_local = local()


def set_thread_local():
    if hasattr(thread_local, 'value'):
        raise ValueError('thread local already present')
    thread_local.value = True


def clear_thread_local(response_or_exc):
    if hasattr(thread_local, 'value'):
        del thread_local.value
    return response_or_exc


def test_teardown_appcontext_is_called(default_app):
    default_app.config['EXECUTOR_MAX_WORKERS'] = 1
    default_app.config['EXECUTOR_PUSH_APP_CONTEXT'] = True
    default_app.teardown_appcontext(clear_thread_local)

    executor = Executor(default_app)
    with default_app.test_request_context():
        futures = [executor.submit(set_thread_local) for _ in range(2)]
        concurrent.futures.wait(futures)
        [propagate_exceptions_callback(future) for future in futures]


try:
    import flask_sqlalchemy
except ImportError:
    flask_sqlalchemy = None


@pytest.mark.skipif(flask_sqlalchemy is None, reason="flask_sqlalchemy not installed")
def test_sqlalchemy(default_app, caplog):
    default_app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'echo_pool': 'debug', 'echo': 'debug'}
    default_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    default_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    default_app.config['EXECUTOR_PUSH_APP_CONTEXT'] = True
    default_app.config['EXECUTOR_MAX_WORKERS'] = 1
    db = flask_sqlalchemy.SQLAlchemy(default_app)

    def test_db():
        return list(db.session.execute('select 1'))

    executor = Executor(default_app)
    with default_app.test_request_context():
        for i in range(2):
            with caplog.at_level('DEBUG'):
                caplog.clear()
                future = executor.submit(test_db)
                concurrent.futures.wait([future])
                future.result()
                assert 'checked out from pool' in caplog.text
                assert 'being returned to pool' in caplog.text
