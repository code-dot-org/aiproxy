import pytest
from lib.assessment.code_feature_extractor import CodeFeatures

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

    lesson="U3L11"

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

    lesson="U3L14"

    code_features.extract_features(code, learning_goal, lesson)

    assert code_features.features["object_types"] == {'shapes': 0, 'sprites': 3, 'text': 0}
    assert code_features.features["movement"] == {'random': 1, 'counter': 1}
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

    lesson="U3L18"

    code_features.extract_features(code, learning_goal, lesson)

    assert code_features.features["object_types"] == {'shapes': 0, 'sprites': 4, 'text': 1}
    assert code_features.features["movement"] == {'random': 0, 'counter': 0}
    assert code_features.assessment == 'Limited Evidence'
