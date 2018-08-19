import concurrent.futures

from flask import current_app

__all__ = ('Executor', )
__version__ = '0.1.4'


class Executor:

    def __init__(self, app=None):
        self.app = app
        self._executor = None
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        app.config.setdefault('EXECUTOR_TYPE', 'thread')
        app.config.setdefault('EXECUTOR_MAX_WORKERS', None)
        app.extensions['executor'] = self

    def _make_executor(self):
        executor_type = current_app.config['EXECUTOR_TYPE']
        executor_max_workers = current_app.config['EXECUTOR_MAX_WORKERS']
        if executor_type == 'thread':
            _executor = concurrent.futures.ThreadPoolExecutor
        elif executor_type == 'process':
            _executor = concurrent.futures.ProcessPoolExecutor
        else:
            raise ValueError('{} is not a valid executor type.'.format(executor_type))
        return _executor(max_workers=executor_max_workers)

    def submit(self, *args, **kwargs):
        if self._executor is None:
            self._executor = self._make_executor()
        return self._executor.submit(*args, **kwargs)

