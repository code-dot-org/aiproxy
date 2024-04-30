# Container for storing decision trees for static assessment of learning goals
class DecisionTrees:
  def __init__(self):
    
    # List of evidence generated during assessment
    self.evidence = []

    # Assessed score
    self.assessment = ''

  # Function to assess a student project using features extracted by code
  # feature extractor and relevant decision tree.
  def assess(self, features, learning_goal, lesson):
    match [learning_goal["Key Concept"], lesson]:
      case ['Position - Elements and the Coordinate System', 'csd3-2023-L11']:
        self.u3l11_position_assessment(features)
      case ['Position and Movement', 'csd3-2023-L14']:
        self.u3l14_position_assessment(features)
      case ['Position and Movement', 'csd3-2023-L18']:
        self.u3l18_position_assessment(features)
      case ['Modularity - Sprites and Sprite Properties', 'csd3-2023-L14']:
        self.u3l14_modularity_assessment(features)
      case ['Modularity - Multiple Sprites', 'csd3-2023-L18']:
        self.u3l18_modularity_assessment(features)

  # Evidence generation functions
  def save_evidence_string(self, start, end, message):
    evidence_string = f"Lines {start}-{end}: {message}" if start != end else f"Line {start}: {message}"
    if evidence_string not in self.evidence:
      self.evidence.append(evidence_string)

  def object_types_evidence(self, data, shapes, sprites, text):
    for obj in data["objects"]:
        if obj["type"] == "shape":
          self.save_evidence_string(obj["start"], obj["end"], f"Code contains {shapes} shape{'s' if shapes > 1 else ''}")
        elif obj["type"] == "sprite":
          self.save_evidence_string(obj["start"], obj["end"], f"Code contains {sprites} sprite{'s' if sprites > 1 else ''}")
        elif obj["type"] == "text":
          self.save_evidence_string(obj["start"], obj["end"], f"Code contains {text} line{'s' if text > 1 else ''} of text")

  def total_objects_evidence(self, data, total_elements):
    for obj in data["objects"]:
        self.save_evidence_string(obj["start"], obj["end"], f"Code contains {total_elements} total element{'s' if total_elements > 1 else ''}")

  def sprites_and_other_elements_evidence(self, data, sprites, other_elements):
    for obj in data["objects"]:
      if obj["type"] == "sprite":
        self.save_evidence_string(obj["start"], obj["end"], f"Code contains {sprites} sprite{'s' if sprites > 1 else ''}")
      else:
        self.save_evidence_string(obj["start"], obj["end"], f"Code contains {other_elements} non-sprite element{'s' if other_elements > 1 else ''}")

  def sprites_evidence(self, data, sprites):
    for obj in data["objects"]:
      if obj["type"] == "sprite":
        self.save_evidence_string(obj["start"], obj["end"], f"Code contains {sprites} sprite{'s' if sprites > 1 else ''}")

  def movement_types_evidence(self, data, random, counter):
    for line in data["movement"]["random"]["lines"]:
        self.save_evidence_string(line["start"], line["end"], f"Code contains {random} instance{'s' if random > 1 else ''} of movement using the randomNumber() function")
    for line in data["movement"]["counter"]["lines"]:
      self.save_evidence_string(line["start"], line["end"], f"Code contains {counter} instance{'s' if counter > 1 else ''} of movement using the counter pattern")

  def object_props_updated_evidence(self, data):
    for prop in data["property_change"]:
      if 'property' in prop:
        self.save_evidence_string(prop["start"], prop["end"], f"{prop['object']} object's {prop['property']} property updated {'in' if prop['draw_loop'] else 'outside of'} the draw loop")
      else:
        self.save_evidence_string(prop["start"], prop["end"], f"{prop['object']} object updated by its {prop['method']} method {'in' if prop['draw_loop'] else 'outside of'} the draw loop")

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
      self.object_types_evidence(data, shapes, sprites, text)
      self.assessment = "Extensive Evidence"

    # Convincing Evidence: At least 1 shape, 2 sprites, and 1 line of text
    elif shapes >= 1 and sprites >= 2 and text >= 1:
      self.object_types_evidence(data, shapes, sprites, text)
      self.assessment = "Convincing Evidence"

    # Limited Evidence: A cumulative of at least a total of 3 elements
    elif total_elements >= 3:
      self.total_objects_evidence(data, total_elements)
      self.assessment =  "Limited Evidence"

    # No Evidence: No elements placed using the coordinate system.
    else:
      self.assessment =  "No Evidence"

  # Function to statically assess U3L14 'Position and Movement'
  def u3l14_position_assessment(self, data):
    shapes = data["object_types"]["shapes"]
    sprites = data["object_types"]["sprites"]
    text = data["object_types"]["text"]
    total_elements = shapes + sprites + text

    random = data["movement"]["random"]["count"]
    counter = data["movement"]["counter"]["count"]
    movement = random + counter

    # Extensive Evidence: At least 2 shapes, 2 sprites, 2 lines of text, and 2 types of movement
    if shapes >= 2 and sprites >= 2 and text >= 2 and random > 0 and counter > 0:
      self.object_types_evidence(data, shapes, sprites, text)
      self.movement_types_evidence(data, random, counter)
      self.assessment = "Extensive Evidence"

    # Convincing Evidence: At least 1 shape, 2 sprites, 1 line of text, and some movement
    elif shapes >= 1 and sprites >= 2 and text >= 1 and movement > 0:
      self.object_types_evidence(data, shapes, sprites, text)
      self.movement_types_evidence(data, random, counter)
      self.assessment = "Convincing Evidence"

    # Limited Evidence: A cumulative of at least a total of 3 elements
    elif total_elements >= 3:
      self.total_objects_evidence(data, total_elements)
      self.assessment = "Limited Evidence"

    # No Evidence: No elements placed using the coordinate system.
    else:
      self.assessment = "No Evidence"

  # Function to statically assess U3L18 'Position and Movement'
  def u3l18_position_assessment(self, data):
    sprites = data["object_types"]["sprites"]
    other_elements = data["object_types"]["shapes"] + data["object_types"]["text"]
    total_elements = sprites + other_elements

    random = data["movement"]["random"]["count"]
    counter = data["movement"]["counter"]["count"]
    movement = random + counter

    # Extensive Evidence: At least 3 sprites, 2 other elements, and 2 types of movement
    if sprites >= 3 and other_elements >= 1 and counter > 0 and random > 0:
      self.sprites_and_other_elements_evidence(data, sprites, other_elements)
      self.movement_types_evidence(data, random, counter)
      self.assessment = "Extensive Evidence"

    # Convincing Evidence: At least 2 sprites, 1 other element, and some movement
    elif sprites >= 2 and other_elements > 0 and movement > 0:
      self.sprites_and_other_elements_evidence(data, sprites, other_elements)
      self.movement_types_evidence(data, random, counter)
      self.assessment = "Convincing Evidence"

    # Limited Evidence: A cumulative of at least a total of 1 element
    elif total_elements >= 1:
      self.total_objects_evidence(data, total_elements)
      self.assessment = "Limited Evidence"

    # No Evidence: No elements placed using the coordinate system.
    else:
      self.assessment = "No Evidence"
  
  def u3l14_modularity_assessment(self, data):
    sprites = data["object_types"]["sprites"]

    sprites_updated_in_draw = set([property["object"] for property in data["property_change"] if
                                   any([obj["identifier"] == property["object"] and
                                        obj["type"]=="sprite" for obj in data["objects"]])
                                  and property["draw_loop"] == True])

    # Extensive Evidence: At least 2 sprites, at least 2 of them have properties updated in the draw loop
    if sprites >= 2 and len(sprites_updated_in_draw) >= 2:
      self.sprites_evidence(data, sprites)
      self.object_props_updated_evidence(data)
      self.assessment = "Extensive Evidence"

    # Convincing Evidence: At least 1 sprites, at least 1 of them have properties updated in the draw loop
    elif sprites >= 1 and len(sprites_updated_in_draw) >= 1:
      self.sprites_evidence(data, sprites)
      self.object_props_updated_evidence(data)
      self.assessment = "Convincing Evidence"

    # Limited Evidence: At least 1 sprites
    elif sprites >= 1:
      self.sprites_evidence(data, sprites)
      self.assessment = "Limited Evidence"

    # No Evidence: No sprites
    else:
      self.assessment = "No Evidence"
  
  def u3l18_modularity_assessment(self, data):
    sprites = data["object_types"]["sprites"]

    sprites_updated_in_draw = set([property["object"] for property in data["property_change"] if
                                   any([obj["identifier"] == property["object"] and
                                        obj["type"]=="sprite" for obj in data["objects"]])
                                  and property["draw_loop"] == True])

    # Extensive Evidence: At least 3 sprites, at least 3 of them have properties updated in the draw loop
    if sprites >= 3 and len(sprites_updated_in_draw) >= 3:
      self.sprites_evidence(data, sprites)
      self.object_props_updated_evidence(data)
      self.assessment = "Extensive Evidence"

    # Convincing Evidence: At least 1 sprites, at least 1 of them have properties updated in the draw loop
    elif sprites >= 1 and len(sprites_updated_in_draw) >= 1:
      self.sprites_evidence(data, sprites)
      self.object_props_updated_evidence(data)
      self.assessment = "Convincing Evidence"

    # Limited Evidence: At least 2 sprites
    elif sprites >= 1:
      self.sprites_evidence(data, sprites)
      self.assessment = "Limited Evidence"

    # No Evidence: No sprites
    else:
      self.assessment = "No Evidence"
