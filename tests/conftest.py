from flask import Flask
import pytest

from flask_executor import Executor


@pytest.fixture(params=['thread', 'process'])
def app(request):
    app = Flask(__name__)
    app.config['EXECUTOR_TYPE'] = request.param
    return app

@pytest.fixture
def default_app():
    app = Flask(__name__)
    return app
