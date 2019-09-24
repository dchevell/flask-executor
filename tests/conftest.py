from flask import Flask
import pytest

from flask_executor import Executor


@pytest.fixture(params=['thread_push_app_context', 'thread_copy_app_context', 'process'])
def app(request):
    app = Flask(__name__)
    app.config['EXECUTOR_TYPE'] = 'process' if request.param == 'process' else 'thread'
    app.config['EXECUTOR_PUSH_APP_CONTEXT'] = request.param == 'thread_push_app_context'

    return app

@pytest.fixture
def default_app():
    app = Flask(__name__)
    return app
