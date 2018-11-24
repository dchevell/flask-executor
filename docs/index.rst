.. Flask-Executor documentation master file, created by
   sphinx-quickstart on Sun Sep 23 18:52:39 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Flask-Executor
==============

.. module:: flask_executor

Flask-Executor is a `Flask`_ extension that makes it easy to work with :py:mod:`concurrent.futures`
in your application.

Installation
------------

Flask-Executor is available on PyPI and can be installed with pip::

    $ pip install flask-executor

Setup
------

The Executor extension can either be initialized directly::

    from flask import Flask
    from flask_executor import Executor

    app = Flask(__name__)
    executor = Executor(app)

Or through the factory method::

    executor = Executor()
    executor.init_app(app)


Configuration
-------------

To specify the type of executor to initialise, set ``EXECUTOR_TYPE`` inside your app configuration.
Valid values are ``'thread'`` (default) to initialise a
:class:`~concurrent.futures.ThreadPoolExecutor`, or ``'process'`` to initialise a
:class:`~concurrent.futures.ProcessPoolExecutor`::

    app.config['EXECUTOR_TYPE'] = 'thread'

To define the number of worker threads for a :class:`~concurrent.futures.ThreadPoolExecutor` or the
number of worker processes for a :class:`~concurrent.futures.ProcessPoolExecutor`, set
``EXECUTOR_MAX_WORKERS`` in your app configuration. Valid values are any integer or ``None`` (default)
to let :py:mod:`concurrent.futures` pick defaults for you::

    app.config['EXECUTOR_MAX_WORKERS'] = 5

If multiple executors are needed, :class:`flask_executor.Executor` can be initialised with a ``name``
parameter. Named executors will look for configuration variables prefixed with the specified ``name``
value, uppercased:

    app.config['CUSTOM_EXECUTOR_TYPE'] = 'thread'
    app.config['CUSTOM_EXECUTOR_MAX_WORKERS'] = 5
    executor = Executor(app, name='custom')


Basic Usage
-----------

Flask-Executor supports the standard :class:`concurrent.futures.Executor` methods,
:meth:`~concurrent.futures.Executor.submit` and :meth:`~concurrent.futures.Executor.map`::

    def fib(n):
        if n <= 2:
            return 1
        else:
            return fib(n-1) + fib(n-2)

    @app.route('/run_fib')
    def run_fib():
        executor.submit(fib, 5)
        executor.map(fib, range(1, 6))
        return 'OK'

Submitting a task via :meth:`~concurrent.futures.Executor.submit` returns a
:class:`flask_executor.FutureProxy` object, a subclass of 
:class:`concurrent.futures.Future` object from which you can retrieve your job status or result.


Contexts
--------

When calling :meth:`~concurrent.futures.Executor.submit` or :meth:`~concurrent.futures.Executor.map`
Flask-Executor will wrap `ThreadPoolExecutor` callables with a copy of both the current application
context and current request context. Code that must be run in these contexts or that depends on
information or configuration stored in :data:`flask.current_app`, :data:`flask.request` or
:data:`flask.g` can be submitted to the executor without modification.


Futures
-------

:class:`flask_executor.FutureProxy` objects look and behave like normal :class:`concurrent.futures.Future`
objects, but allow `flask_executor` to override certain methods and add additional behaviours.
When submitting a callable to :meth:`~concurrent.futures.Future.add_done_callback`, callables are
wrapped with a copy of both the current application context and current request context.

You may want to preserve access to Futures returned from the executor, so that you can retrieve the
results in a different part of your application. Flask-Executor allows Futures to be stored within
the executor itself and provides methods for querying and returning them in different parts of your
app::

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


Decoration
----------

Flask-Executor lets you decorate methods in the same style as distributed task queues like
`Celery`_::

    @executor.job
    def fib(n):
        if n <= 2:
            return 1
        else:
            return fib(n-1) + fib(n-2)

    @app.route('/decorate_fib')
    def decorate_fib():
        fib.submit(5)
        fib.submit_stored('fibonacci', 5)
        fib.map(range(1, 6))
        return 'OK'


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   api/modules



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _Flask: http://flask.pocoo.org/
.. _Celery: http://www.celeryproject.org/
