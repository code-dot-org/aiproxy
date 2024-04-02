import pytest
from lib.assessment.code_feature_extractor import CodeFeatures

@pytest.fixture
def code_features():
    """ Creates a Label() instance for any test that has a 'label' parameter.
    """
    yield CodeFeatures()

class TestCodeFeatureExtractor:
  def test_extract_features_function(self, code_features):
    learning_goal = {"Key Concept": "Position - Elements and the Coordinate System",
                     "Instructions": "CFE",
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

