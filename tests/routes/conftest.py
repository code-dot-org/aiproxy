import pytest

@pytest.fixture(autouse=True)
def mock_requests(requests_mock):
    """ Ensure no network request goes out during route tests, here.
    """
    pass
