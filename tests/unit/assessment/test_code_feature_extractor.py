import pytest
from lib.assessment.code_feature_extractor import CodeFeatures
import esprima

import pprint
pp = pprint.PrettyPrinter(indent=2)

@pytest.fixture
def code_features():
    """ Creates a Label() instance for any test that has a 'label' parameter.
    """
    yield CodeFeatures()

class TestCodeFeatureExtractor:
  def test_feature_extractor(self, code_features):
    code = """function arrakis() {
  noStroke();
  background("yellow");
}

background("blue");
var planet = "caladan";
var shai_hulud = createSprite(100, 275);
var muadib = createSprite(50, 100);
muadib.setAnimation("muadib");
var fremen = createSprite(0, 275);
fremen.setAnimation("fremen");
fremen.velocityY = 1;
shai_hulud.setAnimation("worm");
shai_hulud.velocityX = 2;
function draw() {
  if (planet === "arrakis") {
    arrakis();
  }
  if (planet === "caladan") {
    background("blue")
  }
  rhythm = randomNumber(1, 100);
  muadib.x = muadib.x + 2;
  if (rhythm < 50){
      shai_hulud.visible = False;
    }
  if (muadib.x == shai_hulud.x) {
      muadib.setAnimation("eyes of ibad");
      fremen.setAnimation("lisan al gaib");
  }
}
"""

    code_features.extract_features(code)
    print(code_features.features)
    assert code_features.features == {'conditionals': [{'test': {'left': {'identifier': 'planet'},
                                                                  'operator': '===',
                                                                  'right': {'literal': 'arrakis'},
                                                                  'start': 17,
                                                                  'end': 17},
                                                        'consequent': [{'function': 'arrakis',
                                                                        'args': [],
                                                                        'user_interaction': False,
                                                                        'start': 18,
                                                                        'end': 18}],
                                                        'alternate': [],
                                                        'start': 17,
                                                        'end': 19,
                                                        'draw_loop': True,
                                                        'trigger': 'variable'},
                                                        {'test': {'left': {'identifier': 'planet'},
                                                                  'operator': '===',
                                                                  'right': {'literal': 'caladan'},
                                                                  'start': 20,
                                                                  'end': 20},
                                                        'consequent': [{'function': 'background',
                                                                        'args': {'color': ['blue']},
                                                                        'user_interaction': False,
                                                                        'start': 21,
                                                                        'end': 21}],
                                                        'alternate': [],
                                                        'start': 20,
                                                        'end': 22,
                                                        'draw_loop': True,
                                                        'trigger': 'variable'},
                                                        {'test': {'left': {'identifier': 'rhythm'},
                                                                  'operator': '<',
                                                                  'right': {'literal': 50},
                                                                  'start': 25,
                                                                  'end': 25},
                                                        'consequent': [{'assignee': {'object': 'shai_hulud',
                                                                                      'property': 'visible',
                                                                                      'start': 26,
                                                                                      'end': 26},
                                                                        'value': 'False',
                                                                        'start': 26,
                                                                        'end': 26}],
                                                        'alternate': [],
                                                        'start': 25,
                                                        'end': 27,
                                                        'draw_loop': True,
                                                        'trigger': 'variable'},
                                                        {'test': {'left': {'object': 'muadib',
                                                                          'property': 'x',
                                                                          'start': 28,
                                                                          'end': 28},
                                                                  'operator': '==',
                                                                  'right': {'object': 'shai_hulud',
                                                                            'property': 'x',
                                                                            'start': 28,
                                                                            'end': 28},
                                                                  'start': 28,
                                                                  'end': 28},
                                                        'consequent': [{'function': {'object': 'muadib',
                                                                                      'method': 'setAnimation',
                                                                                      'start': 29,
                                                                                      'end': 29},
                                                                        'args': ['eyes of ibad'],
                                                                        'user_interaction': False,
                                                                        'start': 29,
                                                                        'end': 29},
                                                                        {'function': {'object': 'fremen',
                                                                                      'method': 'setAnimation',
                                                                                      'start': 30,
                                                                                      'end': 30},
                                                                        'args': ['lisan al gaib'],
                                                                        'user_interaction': False,
                                                                        'start': 30,
                                                                        'end': 30}],
                                                        'alternate': [],
                                                        'start': 28,
                                                        'end': 31,
                                                        'draw_loop': True,
                                                        'trigger': 'object'}],
                                      'draw_loop': {'start': 16, 'end': 32},
                                      'movement': {'random': {'count': 0, 'lines': []},
                                                    'counter': {'count': 1, 'lines': [{'start': 24, 'end': 24}]}},
                                      'objects': [{'identifier': '',
                                                    'properties': {'color': ['yellow']},
                                                    'type': 'background',
                                                    'start': 3,
                                                    'end': 3},
                                                  {'identifier': '',
                                                    'properties': {'color': ['blue']},
                                                    'type': 'background',
                                                    'start': 6,
                                                    'end': 6},
                                                  {'identifier': 'shai_hulud',
                                                    'properties': {'x': [100], 'y': [275]},
                                                    'type': 'sprite',
                                                    'start': 8,
                                                    'end': 8},
                                                  {'identifier': 'muadib',
                                                    'properties': {'x': [50], 'y': [100]},
                                                    'type': 'sprite',
                                                    'start': 9,
                                                    'end': 9},
                                                  {'identifier': 'fremen',
                                                    'properties': {'x': [0], 'y': [275]},
                                                    'type': 'sprite',
                                                    'start': 11,
                                                    'end': 11},
                                                  {'identifier': '',
                                                    'properties': {'color': ['blue']},
                                                    'type': 'background',
                                                    'start': 21,
                                                    'end': 21}],
                                      'object_types': {'shapes': 0, 'sprites': 3, 'text': 0},
                                      'property_change': [{'object': 'muadib',
                                                            'method': 'setAnimation',
                                                            'start': 10,
                                                            'end': 10,
                                                            'draw_loop': False},
                                                          {'object': 'fremen',
                                                            'method': 'setAnimation',
                                                            'start': 12,
                                                            'end': 12,
                                                            'draw_loop': False},
                                                          {'object': 'fremen',
                                                            'property': 'velocityY',
                                                            'start': 13,
                                                            'end': 13,
                                                            'draw_loop': False},
                                                          {'object': 'shai_hulud',
                                                            'method': 'setAnimation',
                                                            'start': 14,
                                                            'end': 14,
                                                            'draw_loop': False},
                                                          {'object': 'shai_hulud',
                                                            'property': 'velocityX',
                                                            'start': 15,
                                                            'end': 15,
                                                            'draw_loop': False},
                                                          {'object': 'muadib',
                                                            'property': 'x',
                                                            'start': 24,
                                                            'end': 24,
                                                            'draw_loop': True},
                                                          {'object': 'shai_hulud',
                                                            'property': 'visible',
                                                            'start': 26,
                                                            'end': 26,
                                                            'draw_loop': True},
                                                          {'object': 'muadib',
                                                            'method': 'setAnimation',
                                                            'start': 29,
                                                            'end': 29,
                                                            'draw_loop': True},
                                                          {'object': 'fremen',
                                                            'method': 'setAnimation',
                                                            'start': 30,
                                                            'end': 30,
                                                            'draw_loop': True}],
                                      'user_functions': [{'function': 'arrakis',
                                                          'body': [{'function': 'noStroke',
                                                                    'args': [],
                                                                    'user_interaction': False,
                                                                    'start': 2,
                                                                    'end': 2},
                                                                    {'function': 'background',
                                                                    'args': {'color': ['yellow']},
                                                                    'user_interaction': False,
                                                                    'start': 3,
                                                                    'end': 3}],
                                                          'start': 1,
                                                          'end': 4,
                                                          'calls': 1}],
                                      'function_calls': [{'function': 'noStroke',
                                                          'args': [],
                                                          'user_interaction': False,
                                                          'start': 2,
                                                          'end': 2},
                                                          {'function': 'background',
                                                          'args': {'color': ['yellow']},
                                                          'user_interaction': False,
                                                          'start': 3,
                                                          'end': 3},
                                                          {'function': 'background',
                                                          'args': {'color': ['blue']},
                                                          'user_interaction': False,
                                                          'start': 6,
                                                          'end': 6},
                                                          {'function': {'object': 'muadib',
                                                                        'method': 'setAnimation',
                                                                        'start': 10,
                                                                        'end': 10},
                                                          'args': ['muadib'],
                                                          'user_interaction': False,
                                                          'start': 10,
                                                          'end': 10},
                                                          {'function': {'object': 'fremen',
                                                                        'method': 'setAnimation',
                                                                        'start': 12,
                                                                        'end': 12},
                                                          'args': ['fremen'],
                                                          'user_interaction': False,
                                                          'start': 12,
                                                          'end': 12},
                                                          {'function': {'object': 'shai_hulud',
                                                                        'method': 'setAnimation',
                                                                        'start': 14,
                                                                        'end': 14},
                                                          'args': ['worm'],
                                                          'user_interaction': False,
                                                          'start': 14,
                                                          'end': 14},
                                                          {'function': 'arrakis',
                                                          'args': [],
                                                          'user_interaction': False,
                                                          'start': 18,
                                                          'end': 18},
                                                          {'function': 'background',
                                                          'args': {'color': ['blue']},
                                                          'user_interaction': False,
                                                          'start': 21,
                                                          'end': 21},
                                                          {'function': {'object': 'muadib',
                                                                        'method': 'setAnimation',
                                                                        'start': 29,
                                                                        'end': 29},
                                                          'args': ['eyes of ibad'],
                                                          'user_interaction': False,
                                                          'start': 29,
                                                          'end': 29},
                                                          {'function': {'object': 'fremen',
                                                                        'method': 'setAnimation',
                                                                        'start': 30,
                                                                        'end': 30},
                                                          'args': ['lisan al gaib'],
                                                          'user_interaction': False,
                                                          'start': 30,
                                                          'end': 30}],
                                      'variables': [{'identifier': 'planet',
                                                      'value': 'caladan',
                                                      'start': 7,
                                                      'end': 7}]}

  def test_binary_expression_helper(self, code_features):
    statement = "x = x + 1"
    parsed = esprima.parseScript(statement, {'tolerant': True, 'comment': True, 'loc': True})
    result = code_features.binary_expression_helper(parsed.body[0].expression.right)
    print(result)
    assert result == {'left': {'identifier': 'x'}, 'operator': '+', 'right': {'literal': 1}, 'start': 1, 'end': 1}

    statement = "x = x + -1"
    parsed = esprima.parseScript(statement, {'tolerant': True, 'comment': True, 'loc': True})
    result = code_features.binary_expression_helper(parsed.body[0].expression.right)
    print(result)
    assert result == {'left': {'identifier': 'x'}, 'operator': '+', 'right': -1.0, 'start': 1, 'end': 1}

  def test_update_expression_helper(self, code_features):
    statement = "x++"
    parsed = esprima.parseScript(statement, {'tolerant': True, 'comment': True, 'loc': True})
    result = code_features.update_expression_helper(parsed.body[0].expression)
    assert result == {'argument': 'x', 'operator': '++', 'start': 1, 'end': 1}

    statement = "blah.x++"
    parsed = esprima.parseScript(statement, {'tolerant': True, 'comment': True, 'loc': True})
    result = code_features.update_expression_helper(parsed.body[0].expression)
    assert result == {'argument': {'object': 'blah', 'property':'x', 'start': 1, 'end': 1}, 'operator': '++', 'start': 1, 'end': 1}

  def test_call_expression_helper(self, code_features):
    statement = """x = 1
    test_function(x)"""
    parsed = esprima.parseScript(statement, {'tolerant': True, 'comment': True, 'loc': True})
    result = code_features.call_expression_helper(parsed.body[1].expression)
    assert result == {'args': ['x'], 'function': 'test_function', 'user_interaction': False, 'start': 2, 'end': 2}

  def test_draw_loop_helper(self, code_features):
    statement = """function draw() {
  var x = 1
}"""
    parsed = esprima.parseScript(statement, {'tolerant': True, 'comment': True, 'loc': True})
    result = code_features.draw_loop_helper(parsed.body[0])
    print(result)
    assert result == [{'identifier': 'x', 'value': 1, 'start': 2, 'end': 2}]

  def test_if_statement_helper(self, code_features):
    statement = """if(-1) {
  if(true) {
    var x = 1;
  }
  if(x === 1) {
    x = 2;
  }
  x++;
} else {
  if(x) {
    var y = 2;
  }
  if(x.prop) {
    x = 2
  }
  test_func(1);
  var z = 1
  z = 2
  y--;
}"""
    parsed = esprima.parseScript(statement, {'tolerant': True, 'comment': True, 'loc': True})
    result = code_features.if_statement_helper(parsed.body[0])
    print(result)
    assert result == {'test': -1.0, 
                      'consequent': [{'test': {'literal': True}, 
                                      'consequent': [{'identifier': 'x', 'value': 1, 'start': 3, 'end': 3}], 
                                      'alternate': [], 
                                      'start': 2, 
                                      'end': 4}, 
                                     {'test': {'left': {'identifier': 'x'}, 'operator': '===', 'right': {'literal': 1}, 'start': 5, 'end': 5}, 
                                      'consequent': [{'assignee': 'x', 'value': 2, 'start': 6, 'end': 6}], 
                                      'alternate': [], 'start': 5, 'end': 7}, {'operator': '++', 'argument': 'x', 'start': 8, 'end': 8}], 
                      'alternate': [{'test': {'identifier': 'x'}, 
                                     'consequent': [{'identifier': 'y', 'value': 2, 'start': 11, 'end': 11}], 
                                     'alternate': [], 'start': 10, 'end': 12}, 
                                    {'test': {'object': 'x', 'property': 'prop', 'start': 13, 'end': 13}, 
                                     'consequent': [{'assignee': 'x', 'value': 2, 'start': 14, 'end': 14}], 
                                     'alternate': [], 'start': 13, 'end': 15}, 
                                    {'function': 'test_func', 'args': [1], 'user_interaction': False, 'start': 16, 'end': 16}, 
                                    {'identifier': 'z', 'value': 1, 'start': 17, 'end': 17}, 
                                    {'assignee': 'z', 'value': 2, 'start': 18, 'end': 18}, 
                                    {'operator': '--', 'argument': 'y', 'start': 19, 'end': 19}], 
                      'start': 1, 'end': 20}
  
  def test_flatten_conditional_paths(self, code_features):
    statement = """if(-1) {
var x = 1
  if(true) {
    x = 1;
  }
}"""
    parsed = esprima.parseScript(statement, {'tolerant': True, 'comment': True, 'loc': True})
    conditional = code_features.if_statement_helper(parsed.body[0])
    result = code_features.flatten_conditional_paths(conditional)
    assert result == [{'identifier': 'x', 'value': 1, 'start': 2, 'end': 2}, {'assignee': 'x', 'value': 1, 'start': 4, 'end': 4}]
    
  def test_variable_assignment_helper(self, code_features):
    statement = """var x = 1
x = test_func(1)
x = -1
"""
    parsed = esprima.parseScript(statement, {'tolerant': True, 'comment': True, 'loc': True})
    result = code_features.variable_assignment_helper(parsed.body[1])
    result2 = code_features.variable_assignment_helper(parsed.body[2])
    assert result == {'assignee': 'x', 'value': {'function': 'test_func', 'args': [1], 'user_interaction': False, 'start': 2, 'end': 2}, 'start': 2, 'end': 2}
    assert result2 == {'assignee': 'x', 'value': -1.0, 'start': 3, 'end': 3}
