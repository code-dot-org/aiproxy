# Container for storing decision trees for static assessment of learning goals
class DecisionTrees:
  def __init__(self):
    pass

  # All decision tree functions should receive the code feature dictionary from the
  # CodeFeatureExtractor class when called.
  # Function to statically assess U3L11 'Position - Elements and the Coordinate System'
  def u3l11_position_assessment(self, data):

    shapes = data["object_types"]["shapes"]
    sprites = data["object_types"]["sprites"]
    text = data["object_types"]["text"]
    total_elements = shapes + sprites + text

    # Extensive Evidence: At least 2 shapes, 2 sprites, and 2 lines of text
    if shapes >= 2 and sprites >= 2 and text >= 2:
      return "Extensive Evidence"

    # Convincing Evidence: At least 1 shape, 2 sprites, and 1 line of text
    elif shapes >= 1 and sprites >= 2 and text >= 1:
      return "Convincing Evidence"

    # Limited Evidence: A cumulative of at least a total of 3 elements
    elif total_elements >= 3:
      return "Limited Evidence"

    # No Evidence: No elements placed using the coordinate system.
    return "No Evidence"

  # Function to statically assess U3L14 'Position and Movement'
  def u3l14_position_assessment(self, data):
    shapes = data["object_types"]["shapes"]
    sprites = data["object_types"]["sprites"]
    text = data["object_types"]["text"]
    total_elements = shapes + sprites + text

    random = data["movement"]["random"]
    counter = data["movement"]["counter"]
    movement = random + counter

    # Extensive Evidence: At least 2 shapes, 2 sprites, 2 lines of text, and 2 types of movement
    if shapes >= 2 and sprites >= 2 and text >= 2 and random > 0 and counter > 0:
      return "Extensive Evidence"

    # Convincing Evidence: At least 1 shape, 2 sprites, 1 line of text, and some movement
    elif shapes >= 1 and sprites >= 2 and text >= 1 and movement > 0:
      return "Convincing Evidence"

    # Limited Evidence: A cumulative of at least a total of 3 elements
    elif total_elements >= 3:
      return "Limited Evidence"

    # No Evidence: No elements placed using the coordinate system.
    return "No Evidence"

  # Function to statically assess U3L18 'Position and Movement'
  def u3l18_position_assessment(self, data):
    sprites = data["object_types"]["sprites"]
    other_elements = data["object_types"]["shapes"] + data["object_types"]["text"]
    total_elements = sprites + other_elements

    random = data["movement"]["random"]
    counter = data["movement"]["counter"]
    movement = random + counter

    # Extensive Evidence: At least 3 sprites, 2 other elements, and 2 types of movement
    if sprites >= 3 and other_elements >= 1 and counter > 0 and random > 0:
      return "Extensive Evidence"

    # Convincing Evidence: At least 2 sprites, 1 other element, and some movement
    elif sprites >= 2 and other_elements > 0 and movement > 0:
      return "Convincing Evidence"

    # Limited Evidence: A cumulative of at least a total of 1 element
    elif total_elements >= 1:
      return "Limited Evidence"

    # No Evidence: No elements placed using the coordinate system.
    return "No Evidence"
  
  def u3l14_modularity_assessment(self, data):
    sprites = data["object_types"]["sprites"]

    sprites_updated_in_draw = set([property["object"] for property in data["property_change"] if
                                   any([obj["identifier"] == property["object"] and
                                        obj["type"]=="sprite" for obj in data["objects"]])
                                  and property["draw_loop"] == True])

    # Extensive Evidence: At least 3 sprites, 2 other elements, and 2 types of movement
    if sprites >= 2 and len(sprites_updated_in_draw) >= 2:
      return "Extensive Evidence"

    # Convincing Evidence: At least 2 sprites, 1 other element, and some movement
    elif sprites >= 1 and len(sprites_updated_in_draw) >= 1:
      return "Convincing Evidence"

    # Limited Evidence: A cumulative of at least a total of 1 element
    elif sprites >= 1:
      return "Limited Evidence"

    # No Evidence: No elements placed using the coordinate system.
    return "No Evidence"
  
  def u3l18_modularity_assessment(self, data):
    sprites = data["object_types"]["sprites"]

    sprites_updated_in_draw = set([property["object"] for property in data["property_change"] if
                                   any([obj["identifier"] == property["object"] and
                                        obj["type"]=="sprite" for obj in data["objects"]])
                                  and property["draw_loop"] == True])

    # Extensive Evidence: At least 3 sprites, 2 other elements, and 2 types of movement
    if sprites >= 3 and len(sprites_updated_in_draw) >= 3:
      return "Extensive Evidence"

    # Convincing Evidence: At least 2 sprites, 1 other element, and some movement
    elif sprites >= 1 and len(sprites_updated_in_draw) >= 1:
      return "Convincing Evidence"

    # Limited Evidence: A cumulative of at least a total of 1 element
    elif sprites >= 1:
      return "Limited Evidence"

    # No Evidence: No elements placed using the coordinate system.
    return "No Evidence"
