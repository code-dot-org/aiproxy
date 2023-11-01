import string
import random
import os

import pytest

from src import create_app

import contextlib
import os


@pytest.fixture()
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
    })

    # other setup can go here

    yield app

    # clean up / reset resources here


@pytest.fixture()
def configured_app():
    app = create_app({})
    app.config.update({
        "TESTING": True,
    })

    # other setup can go here

    yield app

    # clean up / reset resources here


@pytest.fixture(autouse=True)
def mock_env_vars():
    """ Ensures env vars are not touched by tests.
    """

    from unittest.mock import patch

    # Ensure the os.environ passes out a new dictionary
    with patch.dict(os.environ, {}, clear=True):
        yield


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def randomstring():
    """ Returns a lambda that can produce a random string of the given length.
    """

    def genrandomstring(N: int = 10):
        return ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=N))

    return genrandomstring
