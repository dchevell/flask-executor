from flask import Flask
import pytest

@pytest.fixture
def app():
    app = Flask(__name__)
    return app
