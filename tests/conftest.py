import pytest


@pytest.fixture
def load_environment():
    from os import environ
    from environ import Env
    backup = environ._data.copy()
    Env.read_env()
    yield
    environ._data = backup
