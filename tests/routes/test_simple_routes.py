def test_config(configured_app):
    """ Just create an app with a configuration.
    """
    pass

def test_index(client):
    """ Tests the index route '/'
    """

    response = client.get('/')
    assert response.status_code == 200
    assert response.data == b'Success.'

def test_json(client):
    """ Tests the test route '/test' that returns an empty JSON object.
    """

    response = client.get('/test')
    assert response.status_code == 200
    assert response.json == {}

def test_numpy(client):
    """ Tests that numpy works via the '/numpy' route.

    We are specifically looking for the result of the dot product of matrix
    'x' and its transform: `x.dot(x.T)`. Since numpy might render that string
    in a variety of possible ways, we look for the first and second part.
    """

    response = client.get('/test/numpy')
    assert response.status_code == 200
    assert b'[[14 32]' in response.data and b'[32 77]]' in response.data
