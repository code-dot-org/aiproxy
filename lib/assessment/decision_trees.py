# Container for storing decision trees for static assessment of learning goals
class DecisionTrees:
  def __init__(self):
    pass

  # All decision tree functions should receive the code feature dictionary from the 
  # CodeFeatureExtractor class when called.
  # Function to statically assess U3L11 'Position - Elements and the Coordinate System'
  def u3l11_position_assessment(self, data):

    shapes = data.get('shapes', 0)
    sprites = data.get('sprites', 0)
    text = data.get('text', 0)
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
