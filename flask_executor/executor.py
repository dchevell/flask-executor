import concurrent.futures
import sys

from flask import copy_current_request_context, current_app
from flask.globals import _app_ctx_stack

from flask_executor.futures import FutureCollection


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
        return (cpu_count() or 1) * workers_multiplier.get(executor_type, 1)
    return None


class ExecutorJob:

    def __init__(self, executor, fn):
        self.executor = executor
        self.fn = fn

    def submit(self, *args, **kwargs):
        future = self.executor.submit(self.fn, *args, **kwargs)
        return future

    def submit_stored(self, future_key, *args, **kwargs):
        future = self.executor.submit_stored(self.fn, future_key, *args, **kwargs)
        return future

    def map(self, *iterables, **kwargs):
        results = self.executor.map(self.fn, *iterables, **kwargs)
        return results


class Executor:
    """An executor interface for :py:mod:`concurrent.futures` designed for working with Flask
    applications.
    """
    def __init__(self, app=None):
        self.app = app
        self._executor = None
        self.futures = FutureCollection()
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Initialise application. This will also intialise the configured executor type:

            * :class:`concurrent.futures.ThreadPoolExecutor`
            * :class:`concurrent.futures.ProcessPoolExecutor`
        """
        app.config.setdefault('EXECUTOR_TYPE', 'thread')
        executor_type = app.config['EXECUTOR_TYPE']
        executor_max_workers = default_workers(executor_type)
        app.config.setdefault('EXECUTOR_MAX_WORKERS', executor_max_workers)
        app.config.setdefault('EXECUTOR_FUTURES_MAX_LENGTH', None)
        futures_max_length = app.config['EXECUTOR_FUTURES_MAX_LENGTH']
        if futures_max_length:
            self.futures.max_length = futures_max_length
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
        """Schedules the callable, fn, to be executed as fn(\*args \**kwargs) and returns a
        :class:`~concurrent.futures.Future` object representing the execution of the callable.

        See also :meth:`concurrent.futures.Executor.submit`.

        Callables are wrapped a copy of the current application context and the current request
        context. Code that depends on information or configuration stored in
        :data:`flask.current_app`, :data:`flask.request` or :data:`flask.g` can be run without
        modification.

        Note: Because callables only have access to *copies* of the application or request contexts
        any changes made to these copies will not be reflected in the original view. Further,
        changes in the original app or request context that occur after the callable is submitted
        will not be available to the callable.

        Example::

            future = executor.submit(pow, 323, 1235)
            print(future.result())

        :param fn: The callable to be executed.
        :param \*args: A list of positional parameters used with
                       the callable.
        :param \**kwargs: A dict of named parameters used with
                          the callable.

        :rtype: concurrent.futures.Future
        """
        fn = self._prepare_fn(fn)
        return self._executor.submit(fn, *args, **kwargs)

    def submit_stored(self, future_key, fn, *args, **kwargs):
        """Submits the callable using :meth:`Executor.submit` and stores the Future in the executor
        via a :class:`~flask_executor.futures.FutureCollection` object available at
        :data:`Executor.futures`. These futures can be retrieved anywhere inside your application
        and queried for status or popped from the collection. Due to memory concerns, the maximum
        length of the FutureCollection is limited, and the oldest Futures will be dropped when the
        limit is exceeded.

        See :class:`flask_executor.futures.FutureCollection` for more information
        on how to query futures in a collection.

        Example::

            @app.route('/start-task')
            def start_task():
                executor.submit_stored('calc_power', pow, 323, 1235)
                return jsonify({'result':'success'})

            @app.route('/get-result')
            def get_result():
                if not executor.futures.done('calc_power'):
                    return jsonify({'status': executor.futures._state('calc_power')})
                future = executor.futures.pop('calc_power')
                return jsonify({'status': done, 'result': future.result()})

        :param future_key: Stores future for the submitted task inside the
                           executor's ``futures`` object with the specified key.
        :param fn: The callable to be executed.
        :param \*args: A list of positional parameters used with
                       the callable.
        :param \**kwargs: A dict of named parameters used with
                          the callable.

        :rtype: concurrent.futures.Future
        """

        future = self.submit(fn, *args, **kwargs)
        self.futures.add(future_key, future)
        return future

    def map(self, fn, *iterables, **kwargs):
        """Submits the callable, fn, and an iterable of arguments to the executor and returns the
        results inside a generator.

        See also :meth:`concurrent.futures.Executor.map`.

        Callables are wrapped a copy of the current application context and the current request
        context. Code that depends on information or configuration stored in
        :data:`flask.current_app`, :data:`flask.request` or :data:`flask.g` can be run without
        modification.

        Note: Because callables only have access to *copies* of the application or request contexts
        any changes made to these copies will not be reflected in the original view. Further,
        changes in the original app or request context that occur after the callable is submitted
        will not be available to the callable.

        :param fn: The callable to be executed.
        :param \*iterables: An iterable of arguments the callable will apply to.
        :param \**kwargs: A dict of named parameters to pass to the underlying executor's
                          :meth:`~concurrent.futures.Executor.map` method.
        """
        fn = self._prepare_fn(fn)
        return self._executor.map(fn, *iterables, **kwargs)

    def job(self, fn):
        """Decorator. Use this to transform functions into `ExecutorJob` instances that can submit
        themselves directly to the executor.

        Example::

            @executor.job
            def fib(n):
                if n <= 2:
                    return 1
                else:
                    return fib(n-1) + fib(n-2)

            future = fib.submit(5)
            results = fib.map(range(1, 6))
        """
        if isinstance(self._executor, concurrent.futures.ProcessPoolExecutor):
            raise TypeError("Can't decorate {}: Executors that use multiprocessing"
                            " don't support decorators".format(fn))
        return ExecutorJob(executor=self, fn=fn)



