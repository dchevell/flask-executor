Flask-Executor
==============

[![Build Status](https://travis-ci.org/dchevell/flask-executor.svg?branch=master)](https://travis-ci.org/dchevell/flask-executor)
[![PyPI Version](https://img.shields.io/pypi/v/Flask-Executor.svg)](https://pypi.python.org/pypi/Flask-Executor)
[![GitHub license](https://img.shields.io/github/license/dchevell/flask-executor.svg)](https://github.com/dchevell/flask-executor/blob/master/LICENSE)

Sometimes you need a simple task queue without the overhead of separate worker processes or powerful-but-complex libraries beyond your requirements. Flask-Executor is an easy to use wrapper for the `concurrent.futures` module that lets you initialise and configure executors via common Flask application patterns. It's a great way to get up and running fast with a lightweight in-process task queue.

Installation
------------

Flask-Executor is available on PyPI and can be installed with:

    pip install flask-executor


Quick start
-----

Here's a quick example of using Flask-Executor inside your Flask application:

```python
from flask import Flask
from flask_executor import Executor

app = Flask(__name__)

executor = Executor(app)


def send_email(recipient, subject, body):
    # Magic to send an email
    return True


@app.route('/signup')
def signup():
    # Do signup form
    executor.submit(send_email, recipient, subject, body)
```


Documentation
-------------

Check out the full documentation at [flask-executor.readthedocs.io](https://flask-executor.readthedocs.io)!
