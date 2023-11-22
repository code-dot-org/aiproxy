# This houses generic tests of supplemental libraries and health
# of the service.

import logging

from flask import Blueprint, request

test_routes = Blueprint('test_routes', __name__)

# A simple JSON response that always succeeds
@test_routes.route('/test')
def test():
    return {}

# A simple failing request
@test_routes.route('/test/exception')
def test_exception():
    raise Exception("This is a test")
    return {}

# A simple post of an error message.
@test_routes.route('/test/error')
def test_error():
    logging.error("This is an error log.")
    return {}

# A simple post of a critical message.
@test_routes.route('/test/critical')
def test_critical():
    logging.critical("This is a critical log.")
    return {}

# A simple 429 failing request.
@test_routes.route('/test/429')
def test_429():
    return "Too many requests", 429

# Test numpy integration
@test_routes.route('/test/numpy')
def test_numpy():
    import numpy
    response = []

    x = numpy.asarray([[1, 2, 3], [4, 5, 6]])
    response.append(str(x))
    response.append(str(x[1, 1:2]))
    response.append(str(x.T))
    response.append(str(x.dot(x.T)))
    response.append(str(x.reshape([3, 2])))

    return "\n<br>\n".join(response)
