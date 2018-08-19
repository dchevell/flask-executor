Flask-Executor
==============

Wraps concurrent.futures for use with Flask.


Setup
-----

Flask-Executor is available on PyPI and can be installed with:

    pip install flask-executor

The Executor Extension can either be initialized directly:

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
