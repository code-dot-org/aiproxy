import pytest
from lib.assessment.code_feature_extractor import CodeFeatures
import esprima

@pytest.fixture
def code_features():
    """ Creates a Label() instance for any test that has a 'label' parameter.
    """
    yield CodeFeatures()

class TestCodeFeatureExtractor:
  def test_u3l11_position_feature_extractor(self, code_features):
    learning_goal = {"Key Concept": "Position - Elements and the Coordinate System",
                     "Extensive Evidence": "At least 2 shapes, 2 sprites, and 2 lines of text are placed correctly on the screen using the coordinate system.",
                     "Convincing Evidence": "At least 1 shape, 2 sprites, and 1 line of text are placed on the screen using the coordinate system.",
                     "Limited Evidence": "A cumulative of at least a total of 3 elements are placed on the screen using the coordinate system (e.g 2 sprites & 1 line of text or 1 sprite, 1 shape, & 1 line of text)",
                     "No Evidence": "No elements (shapes, sprites, or text) are placed on the screen using the coordinate system."
                     }
    code = """background("black");
var animalhead_duck1 = createSprite(352, 200);
var animalhead_frog_1 = createSprite(46, 200);
animalhead_duck1.setAnimation("animalhead_duck1");
animalhead_frog_1.setAnimation("animalhead_frog_1");
animalhead_frog_1.scale = 0.4;
animalhead_duck1.scale = 0.4;
drawSprites();
textSize(20);
fill("white");
text("Fortnite", 175, 200);
rect(50, 240, 75, 25);"""

    lesson="csd3-2023-L11"

    code_features.extract_features(code, learning_goal, lesson)

    assert code_features.features["object_types"] == {'shapes': 1, 'sprites': 2, 'text': 1}
    assert code_features.assessment == 'Convincing Evidence'

  def test_u3l14_position_feature_extractor(self, code_features):
    learning_goal = {"Key Concept": "Position and Movement",
                     "Instructions": "(1) list the name of each sprite placed on the screen. (2) list each shape placed on the screen. (3) list each line of text placed on the screen (4) list the lines of code inside of the draw loop that update the position of sprites, shapes, or text on the screen. (5) list any sprites, shapes, or text that use random movement. (6) list any sprites, shapes, or text that use the counter pattern",
                     "Extensive Evidence": "At least 2 shapes, 2 sprites, and 2 lines of text are placed correctly on the screen using the coordinate system. At least 2 elements move in different ways.",
                     "Convincing Evidence": "At least 1 shape, 2 sprites, and 1 line of text are placed on the screen using the coordinate system. At least 1 element moves during the program.",
                     "Limited Evidence": "A cumulative of at least a total of 3 elements are placed on the screen using the coordinate system (e.g 2 sprites & 1 line of text or 1 sprite, 1 shape, & 1 line of text).",
                     "No Evidence": "No elements (sprites, shapes, or text) are placed on the screen using the coordinate system."
                     }
    code = """var backgroundSprite = createSprite(200, 200);
var snowman = createSprite(200, 200);
snowman.setAnimation("snowman");
snowman.scale = 0.25;
var santa = createSprite(300, 350);
santa.scale = 0.25;
function draw() {
  backgroundSprite.setAnimation("backgroundSprite");
  santa.setAnimation("santa");
  santa.x = santa.x + randomNumber(-1, 1);
  snowman.rotation++;
  drawSprites();
}"""

    lesson="csd3-2023-L14"

    code_features.extract_features(code, learning_goal, lesson)

    assert code_features.features["object_types"] == {'shapes': 0, 'sprites': 3, 'text': 0}
    assert code_features.features["movement"] == {'random': 1, 'counter': 2}
    assert code_features.assessment == 'Limited Evidence'
  
  def test_u3l18_position_feature_extractor(self, code_features):
    learning_goal = {"Key Concept": "Position and Movement",
                     "Instructions": "(1) list all sprites placed on the screen. (2) list all other elements placed on the screen. (3) describe the movement of each sprite and other elements placed on the screen.",
                     "Extensive Evidence": "At least 3 sprites and at least 2 other elements are placed on the screen using the coordinate system. The sprites move in different ways.",
                     "Convincing Evidence": "At least 2 sprites and 1 other element is placed on the screen using the coordinate system. The sprites move during the program.",
                     "Limited Evidence": "At least one element is placed on the screen using the coordinate system.",
                     "No Evidence": "No elements (sprites or shapes) are placed on the screen using the coordinate system."
                     }
    code = """var grass1 = createSprite(200, 200);
grass1.setAnimation("grass1");
var girl = createSprite(200, 70);
girl.setAnimation("girl");
girl.scale = 0.3;
var Boy = createSprite(260, 65);
Boy.setAnimation("Boy");
Boy.scale = 0.3;
var flowers1  = createSprite(360, 85);
flowers1.setAnimation("flower1");
flowers1.scale = 0.2;
drawSprites();

function draw() {
  text("Boy put the puss", 90, 65);
  if (keyDown("Down")) {
    flowers1.rotation = 90;
    drawSprites();
  }
}"""

    lesson="csd3-2023-L18"

    code_features.extract_features(code, learning_goal, lesson)

    assert code_features.features["object_types"] == {'shapes': 0, 'sprites': 4, 'text': 1}
    assert code_features.features["movement"] == {'random': 0, 'counter': 0}
    assert code_features.assessment == 'Limited Evidence'

  def test_u3l14_modularity_feature_extractor(self, code_features):
    learning_goal = {"Key Concept": "Modularity - Sprites and Sprite Properties"
                     }
    code = """var pacman = createSprite(100, 275);
pacman.setAnimation("pacman");
function draw() {
    pac = randomNumber(1, 100);
    pacman.x = pacman.x - 3;
    if (pac < 50){
        pacman.setAnimation("pacman_closed");
      }
}
"""

    lesson="csd3-2023-L14"

    code_features.extract_features(code, learning_goal, lesson)

    assert code_features.features["object_types"] == {'shapes': 0, 'sprites': 1, 'text': 0}
    assert code_features.features["movement"] == {'random': 0, 'counter': 0}
    assert code_features.features["objects"] == [{'end': 1, 'identifier': 'pacman', 'properties': {'x': [100], 'y': [275]}, 'start': 1, 'type': 'sprite'}]
    assert code_features.features["property_change"] == [   {   'draw_loop': False,
                               'end': 2,
                               'method': 'setAnimation',
                               'object': 'pacman',
                               'start': 2},
                           {   'draw_loop': True,
                               'end': 5,
                               'object': 'pacman',
                               'property': 'x',
                               'start': 5},
                           {   'draw_loop': True,
                               'end': 7,
                               'method': 'setAnimation',
                               'object': 'pacman',
                               'start': 7}]
    assert code_features.assessment == 'Convincing Evidence'

  def test_u3l18_modularity_feature_extractor(self, code_features):
    learning_goal = {"Key Concept": "Modularity - Multiple Sprites"
                     }
    code = """var shai_hulud = createSprite(100, 275);
var muadib = createSprite(50, 100);
var fremen = createSprite(0, 275);
shai_hulud.setAnimation("worm");
function draw() {
    rhythm = randomNumber(1, 100);
    muadib.x = muadib.x + 2;
    if (rhythm < 50){
        shai_hulud.visible = False;
      }
    if (muadib.x == shai_hulud.x && rhythm > 50) {
        fremen.setAnimation("lisan al gaib")
    }
}
"""

    lesson="csd3-2023-L18"

    code_features.extract_features(code, learning_goal, lesson)

    assert code_features.features["object_types"] == {'shapes': 0, 'sprites': 3, 'text': 0}
    assert code_features.features["movement"] == {'random': 0, 'counter': 0}
    assert code_features.features["objects"] == [   {   'end': 1,
                       'identifier': 'shai_hulud',
                       'properties': {'x': [100], 'y': [275]},
                       'start': 1,
                       'type': 'sprite'},
                   {   'end': 2,
                       'identifier': 'muadib',
                       'properties': {'x': [50], 'y': [100]},
                       'start': 2,
                       'type': 'sprite'},
                   {   'end': 3,
                       'identifier': 'fremen',
                       'properties': {'x': [0], 'y': [275]},
                       'start': 3,
                       'type': 'sprite'}]
    assert code_features.features["property_change"] == [   {   'draw_loop': False,
                               'end': 4,
                               'method': 'setAnimation',
                               'object': 'shai_hulud',
                               'start': 4},
                           {   'draw_loop': True,
                               'end': 7,
                               'object': 'muadib',
                               'property': 'x',
                               'start': 7},
                           {   'draw_loop': True,
                               'end': 9,
                               'object': 'shai_hulud',
                               'property': 'visible',
                               'start': 9},
                           {   'draw_loop': True,
                               'end': 12,
                               'method': 'setAnimation',
                               'object': 'fremen',
                               'start': 12}]
    assert code_features.assessment == 'Extensive Evidence'

  def test_binary_expression_helper(self, code_features):
    statement = "x = x + 1"
    parsed = esprima.parseScript(statement, {'tolerant': True, 'comment': True, 'loc': True})
    result = code_features.binary_expression_helper(parsed.body[0].expression.right)
    assert result == {'left': 'x', 'operator': '+', 'right': 1, 'start': 1, 'end': 1}

    statement = "x = x + -1"
    parsed = esprima.parseScript(statement, {'tolerant': True, 'comment': True, 'loc': True})
    result = code_features.binary_expression_helper(parsed.body[0].expression.right)
    assert result == {'left': 'x', 'operator': '+', 'right': -1, 'start': 1, 'end': 1}

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
    assert result == {'args': ['x'], 'function': 'test_function', 'start': 2, 'end': 2}

  def test_draw_loop_helper(self, code_features):
    statement = """function draw() {
  var x = 1
}"""
    parsed = esprima.parseScript(statement, {'tolerant': True, 'comment': True, 'loc': True})
    result = code_features.draw_loop_helper(parsed.body[0])
    assert result == [{'identifier': 'x', 'value': 1, 'start': 2, 'end': 2}]

  def test_if_statement_helper(self, code_features):
    statement = """if(-1) {
  if(true) {
    var x = 1;
  }
  if(x === 1) {
    x = 2;
  }
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
}"""
    parsed = esprima.parseScript(statement, {'tolerant': True, 'comment': True, 'loc': True})
    result = code_features.if_statement_helper(parsed.body[0])
    print(result)
    assert result == {'test': -1.0, 'consequent': [{'test': True, 'consequent': [{'identifier': 'x', 'value': 1, 'start': 3, 'end': 3}], 'alternate': [], 'start': 2, 'end': 4}, {'test': {'left': 'x', 'operator': '===', 'right': 1, 'start': 5, 'end': 5}, 'consequent': [{'assignee': 'x', 'value': 2, 'start': 6, 'end': 6}], 'alternate': [], 'start': 5, 'end': 7}], 'alternate': [{'test': 'x', 'consequent': [{'identifier': 'y', 'value': 2, 'start': 10, 'end': 10}], 'alternate': [], 'start': 9, 'end': 11}, {'test': {'object': 'x', 'property': 'prop', 'start': 12, 'end': 12}, 'consequent': [{'assignee': 'x', 'value': 2, 'start': 13, 'end': 13}], 'alternate': [], 'start': 12, 'end': 14}, {'function': 'test_func', 'args': [1], 'start': 15, 'end': 15}, {'identifier': 'z', 'value': 1, 'start': 16, 'end': 16}, {'assignee': 'z', 'value': 2, 'start': 17, 'end': 17}], 'start': 1, 'end': 18}
  
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
    assert result == {'assignee': 'x', 'value': {'function': 'test_func', 'args': [1], 'start': 2, 'end': 2}, 'start': 2, 'end': 2}
    assert result2 == {'assignee': 'x', 'value': -1.0, 'start': 3, 'end': 3}
