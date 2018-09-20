import concurrent.futures
import sys

from flask import copy_current_request_context, current_app
from flask.globals import _app_ctx_stack


__all__ = ('Executor', )
__version__ = '0.4.0'


workers_multiplier = {
        'thread': 1,
        'process': 5
}


def copy_current_app_context(fn):
    app_context = _app_ctx_stack.top
    def wrapper(*args, **kwargs):
        with app_context:
            return fn(*args, **kwargs)
    return wrapper


def default_workers(executor_type):
    if sys.version_info.major == 3 and sys.version_info.minor in (3, 4):
        try:
            from multiprocessing import cpu_count
        except ImportError:
            def cpu_count():
                return None
        return (cpu_count() or 1) * workers_multiplier[executor_type]
    return None


class ExecutorJob:

    def __init__(self, executor, fn):
        self.executor = executor
        self.fn = fn

    def submit(self, *args, **kwargs):
        future = self.executor.submit(self.fn, *args, **kwargs)
        return future


class Executor:

    def __init__(self, app=None):
        self.app = app
        self._executor = None
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        app.config.setdefault('EXECUTOR_TYPE', 'thread')
        executor_type = app.config['EXECUTOR_TYPE']
        executor_max_workers = default_workers(executor_type)
        app.config.setdefault('EXECUTOR_MAX_WORKERS', executor_max_workers)
        self._executor = self._make_executor(app)
        app.extensions['executor'] = self

    def _make_executor(self, app):
        executor_type = app.config['EXECUTOR_TYPE']
        executor_max_workers = app.config['EXECUTOR_MAX_WORKERS']
        if executor_type == 'thread':
            _executor = concurrent.futures.ThreadPoolExecutor
        elif executor_type == 'process':
            _executor = concurrent.futures.ProcessPoolExecutor
        else:
            raise ValueError("{} is not a valid executor type.".format(executor_type))
        return _executor(max_workers=executor_max_workers)

    def _prepare_fn(self, fn):
        if isinstance(self._executor, concurrent.futures.ThreadPoolExecutor):
            fn = copy_current_request_context(fn)
            fn = copy_current_app_context(fn)
        return fn

    def submit(self, fn, *args, **kwargs):
        fn = self._prepare_fn(fn)
        return self._executor.submit(fn, *args, **kwargs)

    def job(self, fn):
        if isinstance(self._executor, concurrent.futures.ProcessPoolExecutor):
            raise TypeError("Can't decorate {}: Executors that use multiprocessing"
                            " don't support decorators".format(fn))
        return ExecutorJob(executor=self, fn=fn)



