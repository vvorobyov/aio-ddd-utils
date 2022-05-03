import pytest


@pytest.fixture
def load_environment():
    import pathlib
    import os
    from environ import Env
    backup = os.environ._data.copy()
    envfile = os.path.dirname(__file__) + '/.env'
    Env.read_env(str(envfile))
    yield
    os.environ._data = backup
