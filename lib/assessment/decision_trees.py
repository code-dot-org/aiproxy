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
      case ['Modularity - Sprites and Sprite Properties', 'csd3-2023-L14']:
        self.u3l14_modularity_assessment(features)
      case ['Position and Movement', 'csd3-2023-L14']:
        self.u3l14_position_assessment(features)
      case ['Algorithms and Control - Conditionals', 'csd3-2023-L18']:
        self.u3l18_algorithms_conditionals_assessment(features)
      case ['Modularity - Multiple Sprites', 'csd3-2023-L18']:
        self.u3l18_modularity_assessment(features)
      case ['Position and Movement', 'csd3-2023-L18']:
        self.u3l18_position_assessment(features)
      case ['Modularity - Multiple Sprites', 'csd3-2023-L21']:
        self.u3l21_modularity_assessment(features)
      case ['Modularity - Multiple Sprites', 'csd3-2023-L24']:
        self.u3l24_modularity_assessment(features)
      case ['Modularity - Use of Functions', 'csd3-2023-L28']:
        self.u3l28_modularity_functions_assess(features)
      # case ['Algorithms and Control - Backgrounds and Variables', 'csd3-2023-L28']:
      #   self.u3l28_algorithms_backgrounds_assess(features)

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

  def animation_evidence(self, data):
    sprite_animations = [prop for prop in data["property_change"] if any([obj["identifier"] == prop["object"] and
                         obj["type"]=="sprite" for obj in data["objects"]]) and 
                         prop["draw_loop"] == False and 
                         "method" in prop.keys() and 
                         prop["method"] == "setAnimation"
                        ]
    for prop in sprite_animations:
      self.save_evidence_string(prop["start"], prop["end"], f"{prop['object']} sprite's animation is properly set")

  def velocity_evidence(self, data):
    velocity_sprites = [prop for prop in data["property_change"] if any([obj["identifier"] == prop["object"] and
                        obj["type"]=="sprite" for obj in data["objects"]]) and 
                        prop["draw_loop"] == False and
                        "property" in prop.keys() and 
                        "velocity" in prop["property"]
                       ]
    for prop in velocity_sprites:
      self.save_evidence_string(prop["start"], prop["end"], f"{prop['object']} object's velocity updated outside of the draw loop")

  def user_trigger_conditional_evidence(self, data):
    for statement in data:
      self.save_evidence_string(statement['start'], statement['end'], "conditional triggered by user interaction")

  def variable_triggered_conditional_evidence(self, data):
    for statement in data:
      self.save_evidence_string(statement['start'], statement['end'], "conditional triggered by variable value")

  def object_triggered_conditional_evidence(self, data):
    for statement in data:
      self.save_evidence_string(statement['start'], statement['end'], "conditional triggered by object property value")

  def function_definition_evidence(self, data):
    for statement in data:
      self.save_evidence_string(statement['start'], statement['end'], f"definition of {statement['function']} function")

  def function_call_evidence(self, data):
    for statement in data:
      self.save_evidence_string(statement['start'], statement['end'], f"call to {statement['function']} function")
      
  # All decision tree functions should receive the code feature dictionary from the
  # CodeFeatureExtractor class when called.
  # Function to statically assess U3L11 'Position - Elements and the Coordinate System'
  def u3l11_position_assessment(self, data):

    shapes = data["object_types"]["shapes"]
    sprites = data["object_types"]["sprites"]
    text = data["object_types"]["text"]
    total_elements = shapes + sprites + text
    self.object_types_evidence(data, shapes, sprites, text)

    # Extensive Evidence: At least 2 shapes, 2 sprites, and 2 lines of text
    if shapes >= 2 and sprites >= 2 and text >= 2:
      self.assessment = "Extensive Evidence"

    # Convincing Evidence: At least 1 shape, 2 sprites, and 1 line of text
    elif shapes >= 1 and sprites >= 2 and text >= 1:
      self.assessment = "Convincing Evidence"

    # Limited Evidence: A cumulative of at least a total of 3 elements
    elif total_elements >= 3:
      self.assessment =  "Limited Evidence"

    # No Evidence: No elements placed using the coordinate system.
    else:
      self.assessment =  "No Evidence"

  def u3l14_modularity_assessment(self, data):
    sprites = data["object_types"]["sprites"]

    sprites_updated_in_draw = set([property["object"] for property in data["property_change"] if
                                   any([obj["identifier"] == property["object"] and
                                        obj["type"]=="sprite" for obj in data["objects"]])
                                  and property["draw_loop"] == True])
    
    self.sprites_evidence(data, sprites)
    self.object_props_updated_evidence(data)

    # Extensive Evidence: At least 2 sprites, at least 2 of them have properties updated in the draw loop
    if sprites >= 2 and len(sprites_updated_in_draw) >= 2:
      self.assessment = "Extensive Evidence"

    # Convincing Evidence: At least 1 sprites, at least 1 of them have properties updated in the draw loop
    elif sprites >= 1 and len(sprites_updated_in_draw) >= 1:
      self.assessment = "Convincing Evidence"

    # Limited Evidence: At least 1 sprites
    elif sprites >= 1:
      self.assessment = "Limited Evidence"

    # No Evidence: No sprites
    else:
      self.assessment = "No Evidence"

  # Function to statically assess U3L14 'Position and Movement'
  def u3l14_position_assessment(self, data):
    shapes = data["object_types"]["shapes"]
    sprites = data["object_types"]["sprites"]
    text = data["object_types"]["text"]
    total_elements = shapes + sprites + text

    random = data["movement"]["random"]["count"]
    counter = data["movement"]["counter"]["count"]
    movement = random + counter
    self.object_types_evidence(data, shapes, sprites, text)
    self.movement_types_evidence(data, random, counter)

    # Extensive Evidence: At least 2 shapes, 2 sprites, 2 lines of text, and 2 types of movement
    if shapes >= 2 and sprites >= 2 and text >= 2 and random > 0 and counter > 0:
      self.assessment = "Extensive Evidence"

    # Convincing Evidence: At least 1 shape, 2 sprites, 1 line of text, and some movement
    elif shapes >= 1 and sprites >= 2 and text >= 1 and movement > 0:
      self.assessment = "Convincing Evidence"

    # Limited Evidence: A cumulative of at least a total of 3 elements
    elif total_elements >= 3:
      self.assessment = "Limited Evidence"

    # No Evidence: No elements placed using the coordinate system.
    else:
      self.assessment = "No Evidence"

  def u3l18_algorithms_conditionals_assessment(self, data):

    # Retrieve all conditionals executed in the draw loop
    conditionals_in_draw_loop = [statement for statement in data["conditionals"] if statement['draw_loop']]
    
    # Retrieve all conditionals executed in the draw loop that are triggered by user interaction
    user_triggered_conditionals = [statement for statement in conditionals_in_draw_loop if statement['trigger'] == 'user']
    self.user_trigger_conditional_evidence(user_triggered_conditionals)

    # Retrieve all conditionals executed in the draw loop that are triggered by a variable value
    variable_triggered_conditionals = [statement for statement in conditionals_in_draw_loop if statement['trigger'] == 'variable']
    self.variable_triggered_conditional_evidence(variable_triggered_conditionals)

    # Retrieve all conditionals executed in the draw loop that are triggered by an object property value
    object_triggered_conditionals = [statement for statement in conditionals_in_draw_loop if statement['trigger'] == 'object']
    self.object_triggered_conditional_evidence(object_triggered_conditionals)

    # Extensive Evidence: Your program uses at least 3 conditionals inside the draw loop - 
    # 1 (or more) responds to user input and 1 (or more) is triggered by a variable or sprite property.
    if len(conditionals_in_draw_loop) >= 3 and user_triggered_conditionals and (variable_triggered_conditionals or object_triggered_conditionals):
      self.assessment = "Extensive Evidence"

    # Convincing Evidence: Your program uses at least 2 conditionals inside the draw loop - 
    # 1 that responds to user input and 1 that is triggered by a variable or sprite property.
    elif len(conditionals_in_draw_loop) >= 2 and user_triggered_conditionals and (variable_triggered_conditionals or object_triggered_conditionals):
      self.assessment = "Convincing Evidence"
    # Limited Evidence: Your program either has conditionals that all respond to user input 
    # (or all using sprite properties/variables) or only has 1 conditional inside the draw loop.
    elif len(conditionals_in_draw_loop) >= 1 and (user_triggered_conditionals or variable_triggered_conditionals or object_triggered_conditionals):
      self.assessment = "Limited Evidence"

    # No Evidence: Your program does not use any conditionals.
    else:
      self.assessment = "No Evidence"

  def u3l18_modularity_assessment(self, data):
    sprites = data["object_types"]["sprites"]

    # set of sprites that have a property set inside the drawloop (including calling setAnimation)
    sprites_updated_in_draw = set([property["object"] for property in data["property_change"] if
                                   any([obj["identifier"] == property["object"] and
                                        obj["type"]=="sprite" for obj in data["objects"]])
                                  and property["draw_loop"] == True])
    
    self.sprites_evidence(data, sprites)
    self.object_props_updated_evidence(data)
    
    # Extensive Evidence: At least 3 sprites, at least 3 of them have properties updated in the draw loop
    if sprites >= 3 and len(sprites_updated_in_draw) >= 3:
      self.assessment = "Extensive Evidence"

    # Convincing Evidence: At least 1 sprites, at least 1 of them have properties updated in the draw loop
    elif sprites >= 1 and len(sprites_updated_in_draw) >= 1:
      self.assessment = "Convincing Evidence"

    # Limited Evidence: At least 2 sprites
    elif sprites >= 1:
      self.assessment = "Limited Evidence"

    # No Evidence: No sprites
    else:
      self.assessment = "Limited Evidence"

  # Function to statically assess U3L18 'Position and Movement'
  def u3l18_position_assessment(self, data):
    sprites = data["object_types"]["sprites"]
    other_elements = data["object_types"]["shapes"] + data["object_types"]["text"]
    total_elements = sprites + other_elements

    random = data["movement"]["random"]["count"]
    counter = data["movement"]["counter"]["count"]
    movement = random + counter
    self.sprites_and_other_elements_evidence(data, sprites, other_elements)
    self.movement_types_evidence(data, random, counter)

    # Extensive Evidence: At least 3 sprites, 2 other elements, and 2 types of movement
    if sprites >= 3 and other_elements >= 1 and counter > 0 and random > 0:
      self.assessment = "Extensive Evidence"

    # Convincing Evidence: At least 2 sprites, 1 other element, and some movement
    elif sprites >= 2 and other_elements > 0 and movement > 0:
      self.assessment = "Convincing Evidence"

    # Limited Evidence: A cumulative of at least a total of 1 element
    elif total_elements >= 1:
      self.assessment = "Limited Evidence"

    # No Evidence: No elements placed using the coordinate system.
    else:
      self.assessment = "No Evidence"

  def u3l21_modularity_assessment(self, data):
    sprites = data["object_types"]["sprites"]

    # set of sprites that have their animation set outside the drawloop
    animation_set = set([property["object"] for property in data["property_change"] if
                                   any([obj["identifier"] == property["object"] and
                                        obj["type"]=="sprite" for obj in data["objects"]])
                                  and property["draw_loop"] == False
                                  and "method" in property.keys()
                                  and property["method"] == "setAnimation"
                                  ])
    
    # set of sprites that have velocity set outside the drawloop
    velocity_set = set([property["object"] for property in data["property_change"] if
                                   any([obj["identifier"] == property["object"] and
                                        obj["type"]=="sprite" for obj in data["objects"]])
                                  and property["draw_loop"] == False
                                  and "property" in property.keys()
                                  and "velocity" in property["property"]
                                  ])
    
    self.sprites_evidence(data, sprites)
    self.animation_evidence(data)
    self.velocity_evidence(data)

    # Extensive Evidence: At least 3 sprites created and animations set properly. 
    # The x velocity of the target and obstacle properly set outside the draw loop.
    if sprites >= 3 and len(animation_set) >= 3 and len(velocity_set) >= 2:
      self.assessment = "Extensive Evidence"

    # Convincing Evidence: At least 2 sprites created and animations set properly. 
    # The x velocity of the target or obstacle properly set outside the draw loop.
    elif sprites >= 2 and len(animation_set) >= 2 and len(velocity_set) >= 1:
      self.assessment = "Convincing Evidence"

    # Limited Evidence: At least 2 sprites created and animations set. 
    # The x velocity of the target or obstacle not set or set inside the draw loop.
    elif sprites >= 2 and len(animation_set) >= 2:
      self.assessment = "Limited Evidence"

    # No Evidence: No sprites are used in the program.
    else:
      self.assessment = "No Evidence"

  def u3l24_modularity_assessment(self, data):
    sprites = data["object_types"]["sprites"]

    # set of sprites that have their animation set outside the drawloop
    animation_set = set([property["object"] for property in data["property_change"] if
                                   any([obj["identifier"] == property["object"] and
                                        obj["type"]=="sprite" for obj in data["objects"]])
                                  and property["draw_loop"] == False
                                  and "method" in property.keys()
                                  and property["method"] == "setAnimation"
                                  ])
    
    # set of sprites that have velocity set outside the drawloop
    velocity_set = set([property["object"] for property in data["property_change"] if
                                   any([obj["identifier"] == property["object"] and
                                        obj["type"]=="sprite" for obj in data["objects"]])
                                  and property["draw_loop"] == False
                                  and "property" in property.keys()
                                  and "velocity" in property["property"]
                                  ])
    
    self.sprites_evidence(data, sprites)
    self.animation_evidence(data)
    self.velocity_evidence(data)

    # Extensive Evidence: At least 4 sprites are created and their animations are set properly. 
    # The velocities of at least 2 obstacle sprites are properly set outside the draw loop.
    if sprites >= 4 and len(animation_set) >= 4 and len(velocity_set) >= 2:
      self.assessment = "Extensive Evidence"

    # Convincing Evidence: At least 3 sprites are created and their animations are set properly. 
    # The velocity of at least 1 obstacle sprite is properly set outside the draw loop.
    elif sprites >= 3 and len(animation_set) >= 3 and len(velocity_set) >= 1:
      self.assessment = "Convincing Evidence"

    # Limited Evidence: At least 2 sprites were created and their animations were set. 
    # There are no velocities for obstacles set properly outside the draw loop.
    elif sprites >= 2 and len(animation_set) >= 2:
      self.assessment = "Limited Evidence"

    # No Evidence: Either the program only contains the “player” sprite provided by the starter code, 
    # or the sprites are not properly created.
    else:
      self.assessment = "No Evidence"

  def u3l28_modularity_functions_assess(self, data):
    user_functions = [func for func in data["user_functions"] if "draw_loop" not in func]
    function_calls = [call for call in data["function_calls"] if call["function"] in [func["function"] for func in user_functions]]

    call_count = [func['calls'] for func in data["user_functions"]]

    multiple_calls = len([call for call in call_count if call > 1])
    single_calls = len([call for call in call_count if call > 0])

    self.function_definition_evidence(user_functions)
    self.function_call_evidence(function_calls)

    # Extensive Evidence: At least three functions are created outside the draw loop and used to organize your code into logical segments. 
    # At least one of these functions is called multiple times in your program.
    if len(user_functions) >= 3 and multiple_calls > 0:
      self.assessment = "Extensive Evidence"

    # Convincing Evidence: At least two functions are created outside the draw loop and used in your program to organize your code into logical segments.
    elif len(user_functions) >= 2 and single_calls > 0:
      self.assessment = "Convincing Evidence"
      
    # Limited Evidence: At least one function is created outside the draw loop and used in your program.,
    elif len(user_functions) >= 1 and single_calls > 0:
      self.assessment = "Limited Evidence"

    # No Evidence: There are no functions created outside the draw loop and used in your program.
    else:
      self.assessment = "No Evidence"
