import pytest
from lib.assessment.decision_trees import DecisionTrees
import esprima

@pytest.fixture
def decision_trees():
    """ Creates a Label() instance for any test that has a 'label' parameter.
    """
    yield DecisionTrees()

class TestDecisionTrees:
  def test_assess_u3l11_position(self, decision_trees):
    learning_goal = {"Key Concept": "Position - Elements and the Coordinate System"}
    lesson="csd3-2023-L11"
    features = {'object_types': {'shapes': 1, 'sprites': 2, 'text': 1}, 
                'variables': [], 
                'objects': [{'identifier': '', 'properties': {'color': ['black']}, 'type': 'background', 'start': 1, 'end': 1}, {'identifier': 'animalhead_duck1', 'properties': {'x': [352], 'y': [200]}, 'type': 'sprite', 'start': 2, 'end': 2}, {'identifier': 'animalhead_frog_1', 'properties': {'x': [46], 'y': [200]}, 'type': 'sprite', 'start': 3, 'end': 3}, {'identifier': '', 'properties': {'str': ['Fortnite'], 'x': [175], 'y': [200]}, 'type': 'text', 'start': 11, 'end': 11}, {'identifier': '', 'properties': {'x': [50], 'y': [240], 'w': [75], 'h': [25]}, 'type': 'shape', 'start': 12, 'end': 12}], 
                'movement': {'random': {'count': 0, 'lines': []}, 'counter': {'count': 0, 'lines': []}}, 
                'property_change': [{'object': 'animalhead_duck1', 'method': 'setAnimation', 'start': 4, 'end': 4, 'draw_loop': False}, {'object': 'animalhead_frog_1', 'method': 'setAnimation', 'start': 5, 'end': 5, 'draw_loop': False}, {'object': 'animalhead_frog_1', 'property': 'scale', 'start': 6, 'end': 6, 'draw_loop': False}, {'object': 'animalhead_duck1', 'property': 'scale', 'start': 7, 'end': 7, 'draw_loop': False}]}
    decision_trees.assess(features, learning_goal, lesson)
    assert decision_trees.assessment == 'Convincing Evidence'
    assert decision_trees.evidence == ['Line 2: Code contains 2 sprites', 
                                       'Line 3: Code contains 2 sprites', 
                                       'Line 11: Code contains 1 line of text', 
                                       'Line 12: Code contains 1 shape']

  def test_assess_u3l14_position(self, decision_trees):
    learning_goal = {"Key Concept": "Position and Movement"}
    lesson = "csd3-2023-L14"
    features = {'object_types': {'shapes': 0, 'sprites': 3, 'text': 0}, 
                'variables': [], 
                'objects': [{'identifier': 'backgroundSprite', 'properties': {'x': [200], 'y': [200]}, 'type': 'sprite', 'start': 1, 'end': 1}, {'identifier': 'snowman', 'properties': {'x': [200], 'y': [200]}, 'type': 'sprite', 'start': 2, 'end': 2}, {'identifier': 'santa', 'properties': {'x': [300], 'y': [350]}, 'type': 'sprite', 'start': 5, 'end': 5}], 
                'movement': {'random': {'count': 1, 'lines': [{'start': 10, 'end': 10}]}, 'counter': {'count': 2, 'lines': [{'start': 10, 'end': 10}, {'start': 11, 'end': 11}]}}, 
                'property_change': [{'object': 'snowman', 'method': 'setAnimation', 'start': 3, 'end': 3, 'draw_loop': False}, {'object': 'snowman', 'property': 'scale', 'start': 4, 'end': 4, 'draw_loop': False}, {'object': 'santa', 'property': 'scale', 'start': 6, 'end': 6, 'draw_loop': False}, {'object': 'backgroundSprite', 'method': 'setAnimation', 'start': 8, 'end': 8, 'draw_loop': True}, {'object': 'santa', 'method': 'setAnimation', 'start': 9, 'end': 9, 'draw_loop': True}, {'object': 'santa', 'property': 'x', 'start': 10, 'end': 10, 'draw_loop': True}, {'object': 'snowman', 'property': 'rotation', 'start': 11, 'end': 11, 'draw_loop': True}]}

    decision_trees.assess(features, learning_goal, lesson)
    assert decision_trees.assessment == 'Limited Evidence'
    assert decision_trees.evidence == ['Line 1: Code contains 3 total elements',
                                       'Line 2: Code contains 3 total elements',
                                       'Line 5: Code contains 3 total elements',]
    
  def test_assess_u3l18_position(self, decision_trees):
    learning_goal = {"Key Concept": "Position and Movement"}
    lesson="csd3-2023-L18"
    features = {'object_types': {'shapes': 0, 'sprites': 4, 'text': 1}, 
                'variables': [], 
                'objects': [{'identifier': 'grass1', 'properties': {'x': [200], 'y': [200]}, 'type': 'sprite', 'start': 1, 'end': 1}, {'identifier': 'girl', 'properties': {'x': [200], 'y': [70]}, 'type': 'sprite', 'start': 3, 'end': 3}, {'identifier': 'Boy', 'properties': {'x': [260], 'y': [65]}, 'type': 'sprite', 'start': 6, 'end': 6}, {'identifier': 'flowers1', 'properties': {'x': [360], 'y': [85]}, 'type': 'sprite', 'start': 9, 'end': 9}, {'identifier': '', 'properties': {'str': ['Boy put the puss'], 'x': [90], 'y': [65]}, 'type': 'text', 'start': 15, 'end': 15}], 
                'movement': {'random': {'count': 0, 'lines': []}, 'counter': {'count': 0, 'lines': []}}, 
                'property_change': [{'object': 'grass1', 'method': 'setAnimation', 'start': 2, 'end': 2, 'draw_loop': False}, {'object': 'girl', 'method': 'setAnimation', 'start': 4, 'end': 4, 'draw_loop': False}, {'object': 'girl', 'property': 'scale', 'start': 5, 'end': 5, 'draw_loop': False}, {'object': 'Boy', 'method': 'setAnimation', 'start': 7, 'end': 7, 'draw_loop': False}, {'object': 'Boy', 'property': 'scale', 'start': 8, 'end': 8, 'draw_loop': False}, {'object': 'flowers1', 'method': 'setAnimation', 'start': 10, 'end': 10, 'draw_loop': False}, {'object': 'flowers1', 'property': 'scale', 'start': 11, 'end': 11, 'draw_loop': False}, {'object': 'flowers1', 'property': 'rotation', 'start': 17, 'end': 17, 'draw_loop': True}]}
    
    decision_trees.assess(features, learning_goal, lesson)
    assert decision_trees.assessment == 'Limited Evidence'
    assert decision_trees.evidence == ['Line 1: Code contains 5 total elements', 
                                       'Line 3: Code contains 5 total elements', 
                                       'Line 6: Code contains 5 total elements', 
                                       'Line 9: Code contains 5 total elements', 
                                       'Line 15: Code contains 5 total elements']
    
  def test_assess_u3l14_modularity(self, decision_trees):
    learning_goal = {"Key Concept": "Modularity - Sprites and Sprite Properties"}
    lesson="csd3-2023-L14"
    features = {'object_types': {'shapes': 0, 'sprites': 1, 'text': 0}, 
                'variables': [], 
                'objects': [{'identifier': 'pacman', 'properties': {'x': [100], 'y': [275]}, 'type': 'sprite', 'start': 1, 'end': 1}], 
                'movement': {'random': {'count': 0, 'lines': []}, 'counter': {'count': 1, 'lines': [{'start': 5, 'end': 5}]}}, 
                'property_change': [{'object': 'pacman', 'method': 'setAnimation', 'start': 2, 'end': 2, 'draw_loop': False}, {'object': 'pacman', 'property': 'x', 'start': 5, 'end': 5, 'draw_loop': True}, {'object': 'pacman', 'method': 'setAnimation', 'start': 7, 'end': 7, 'draw_loop': True}]}
    decision_trees.assess(features, learning_goal, lesson)
    assert decision_trees.assessment == 'Convincing Evidence'
    assert decision_trees.evidence == ['Line 1: Code contains 1 sprite', 
                                       'Line 2: pacman object updated by its setAnimation method outside of the draw loop', 
                                       "Line 5: pacman object's x property updated in the draw loop", 
                                       'Line 7: pacman object updated by its setAnimation method in the draw loop']
    
  def test_assess_u3l18_modularity(self, decision_trees):
    learning_goal = {"Key Concept": "Modularity - Multiple Sprites"}
    lesson = "csd3-2023-L18"
    features = {'object_types': {'shapes': 0, 'sprites': 3, 'text': 0}, 
                'variables': [], 
                'objects': [{'identifier': 'shai_hulud', 'properties': {'x': [100], 'y': [275]}, 'type': 'sprite', 'start': 1, 'end': 1}, {'identifier': 'muadib', 'properties': {'x': [50], 'y': [100]}, 'type': 'sprite', 'start': 2, 'end': 2}, {'identifier': 'fremen', 'properties': {'x': [0], 'y': [275]}, 'type': 'sprite', 'start': 3, 'end': 3}], 
                'movement': {'random': {'count': 0, 'lines': []}, 'counter': {'count': 1, 'lines': [{'start': 7, 'end': 7}]}}, 
                'property_change': [{'object': 'shai_hulud', 'method': 'setAnimation', 'start': 4, 'end': 4, 'draw_loop': False}, {'object': 'muadib', 'property': 'x', 'start': 7, 'end': 7, 'draw_loop': True}, {'object': 'shai_hulud', 'property': 'visible', 'start': 9, 'end': 9, 'draw_loop': True}, {'object': 'fremen', 'method': 'setAnimation', 'start': 12, 'end': 12, 'draw_loop': True}]}
    
    decision_trees.assess(features, learning_goal, lesson)
    assert decision_trees.assessment == 'Extensive Evidence'
    print(decision_trees.evidence)
    assert decision_trees.evidence == ['Line 1: Code contains 3 sprites', 
                                       'Line 2: Code contains 3 sprites', 
                                       'Line 3: Code contains 3 sprites', 
                                       'Line 4: shai_hulud object updated by its setAnimation method outside of the draw loop', 
                                       "Line 7: muadib object's x property updated in the draw loop", 
                                       "Line 9: shai_hulud object's visible property updated in the draw loop", 
                                       'Line 12: fremen object updated by its setAnimation method in the draw loop']

  def test_save_evidence_string_generates_valid_strings(self, decision_trees):
    decision_trees.save_evidence_string(1, 2, "multiple line evidence test")
    decision_trees.save_evidence_string(3, 3, "single line evidence test")
    assert decision_trees.evidence == ["Lines 1-2: multiple line evidence test", "Line 3: single line evidence test"]

  def test_sprites_and_other_elements_evidence_method(self, decision_trees):
    data = {'objects': [{'identifier': '', 'properties': {'color': ['black']}, 'type': 'background', 'start': 1, 'end': 1}, {'identifier': 'animalhead_duck1', 'properties': {'x': [352], 'y': [200]}, 'type': 'sprite', 'start': 2, 'end': 2}, {'identifier': 'animalhead_frog_1', 'properties': {'x': [46], 'y': [200]}, 'type': 'sprite', 'start': 3, 'end': 3}, {'identifier': '', 'properties': {'str': ['Fortnite'], 'x': [175], 'y': [200]}, 'type': 'text', 'start': 11, 'end': 11}, {'identifier': '', 'properties': {'x': [50], 'y': [240], 'w': [75], 'h': [25]}, 'type': 'shape', 'start': 12, 'end': 12}]}
    sprites = 3
    other_elements = 3
    decision_trees.sprites_and_other_elements_evidence(data, sprites, other_elements)
    print(decision_trees.evidence)
    assert decision_trees.evidence == ['Line 1: Code contains 3 non-sprite elements', 
                                       'Line 2: Code contains 3 sprites', 
                                       'Line 3: Code contains 3 sprites', 
                                       'Line 11: Code contains 3 non-sprite elements', 
                                       'Line 12: Code contains 3 non-sprite elements']
    
  def test_movement_types_evidence_method(self, decision_trees):
    data = {'movement': {'random': {'count': 1, 'lines': [{'start': 10, 'end': 10}]}, 'counter': {'count': 2, 'lines': [{'start': 10, 'end': 10}, {'start': 11, 'end': 11}]}}}
    random = 1
    counter = 2
    decision_trees.movement_types_evidence(data, random, counter)
    print(decision_trees.evidence)
    assert decision_trees.evidence == ['Line 10: Code contains 1 instance of movement using the randomNumber() function', 
                                       'Line 10: Code contains 2 instances of movement using the counter pattern', 
                                       'Line 11: Code contains 2 instances of movement using the counter pattern']