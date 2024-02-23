class DecisionTrees:
  def __init__(self):
    pass

  def assess_position_elements(data):
    """
    Assess Position - Elements and the Coordinate System.

    Parameters:
    data (dict): A dictionary with keys 'shapes', 'sprites', 'text', indicating the number of each element placed correctly.

    Returns:
    str: The level of evidence ("Extensive Evidence", "Convincing Evidence", "Limited Evidence", "No Evidence").
    """
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
        # Ensuring it doesn't fall under higher categories by chance with specific combinations
        if not (shapes >= 1 and sprites >= 2) and  not (shapes >= 2 and text >= 2):
            return "Limited Evidence"

    # No Evidence: No elements placed using the coordinate system.
    return "No Evidence"
