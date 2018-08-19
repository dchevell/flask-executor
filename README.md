Flask-Executor
==============

[![Build Status](https://travis-ci.org/dchevell/flask-executor.svg?branch=master)](https://travis-ci.org/dchevell/flask-executor)
[![PyPI Version](https://img.shields.io/pypi/v/Flask-Executor.svg)](https://pypi.python.org/pypi/Flask-Executor)
[![GitHub license](https://img.shields.io/github/license/dchevell/flask-executor.svg)](https://github.com/dchevell/flask-executor/blob/master/LICENSE)

Sometimes you need a simple task queue without the overhead of managing separate worker processes or dealing with powerful-but-complex libraries beyond your requirements. Flask-Executor is an easy to use wrapper for the `concurrent.futures` module that lets you initialise and configure executors via common Flask application patterns. It's a great way to get up and running fast with a lightweight in-process task queue.


Setup
-----

Flask-Executor is available on PyPI and can be installed with:

    pip install flask-executor

The Executor extension can either be initialized directly:

```python
from flask import Flask
from flask_executor import Executor

app = Flask(__name__)
app.config['EXECUTOR_TYPE'] = 'thread'
app.config['EXECUTOR_MAX_WORKERS'] = 5

executor = Executor(app)
```

Or through the factory method:

```python
executor = Executor()

executor.init_app(app)
```


Configuration
-----

Specify which kind of executor to initialise:

```python
app.config['EXECUTOR_TYPE']
```
Valid values are 'thread' (default) to initialise a ThreadPoolExecutor, or 'process' to initialise a ProcessPoolExecutor.

```python
app.config['EXECUTOR_TYPE'] = 'process'
```

Define the number of worker threads for a ThreadPoolExecutor, or the number of worker processes for a ProcessPoolExecutor:

```python
app.config['EXECUTOR_MAX_WORKERS'] = 5
```
Valid values are any integer, or None (default) to let the concurrent.futures module pick defaults for you.


Usage
-----

You can submit examples to the executor just as you would expect:

```python
from flask import Flask
from flask_executor import Executor

app = Flask(__name__)
executor = Executor(app)

def fib(n):
    if n <= 2:
        return 1
    else:
        return fib(n-1) + fib(n-2)

@app.route('/example1')
def example1():
    executor.submit(fib, 5)
    return 'OK'
```

Submitting examples to the executor returns normal `concurrent.futures.Future` objects that you can work with:

```python
import concurrent.futures
from flask import Response

@app.route('/example2')
def example2():
    future = executor.submit(fib, 5)
    return str(future.result())

@app.route('/job3')
def job3():
    futures = [executor.submit(fib, i) for i in range(1, 40)]
    def generate():
        for future in concurrent.futures.as_completed(futures):
            yield str(future.result()) + '\n'
    return Response(generate(), mimetype='text/text')
```
