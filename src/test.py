# This houses generic tests of supplemental libraries and health
# of the service.

import logging

from flask import Blueprint, request, jsonify

test_routes = Blueprint('test_routes', __name__)

# A simple JSON response that always succeeds
@test_routes.route('/test')
def test():
    return {}

# A simple JSON response that always succeeds
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
