import esprima
from lib.assessment.decision_trees import DecisionTrees
import logging

'''
This class contains delegate and helper functions to extract relevant features from code for assessment. 
New features should be added to the features dictionary.
Add delegate function definitions to the extractCodeFeatures function.
'''
class CodeFeatures:

  def __init__(self):

    # Add additional features here
    self.features = {'shapes': 0, 'sprites': 0, 'text': 0}

    # Store relevant parse tree nodes here during extraction. This will be useful
    # For returning metadata like line and column numbers or for exploring additional
    # info about the extracted features
    self.nodes = []

    # Store statically assessed score here
    self.assessment = ''

  # Feature extraction and labeling functions
    
  # Helper function to check number of arguments in an expression
  # Can be modified to provide additional info about arguments
  def argumentHelper(self, expression):
    return True if len(expression.arguments) >= 2 else False

  # Helper function that returns the type of a called expression
  def expressionHelper(self, expression):
    shapes = ['rect', 'ellipse', 'circle', 'quad', 'triangle']
    if expression.callee.name in shapes and self.argumentHelper(expression):
      return 'shapes'
    elif expression.callee.name == 'text' and self.argumentHelper(expression):
      return 'text'
    elif expression.callee.name == 'createSprite' and self.argumentHelper(expression):
      return 'sprites'
    else:
      return None

  # All delegate functions and code feature extraction 
  def extract_features(self, program, learning_goal):

    # Delegate function for U3L11 'Position - Elements and the Coordinate System'
    # Add additional delegate functions here
    def positionElementsAndTheCoordinateSystemDelegate(node, metadata):
      if node.type == 'ExpressionStatement' and node.expression.type == 'CallExpression':
        func_type = self.expressionHelper(node.expression)
        if func_type:
          self.features[func_type] += 1
          self.nodes.append(node)
      elif node.type == 'VariableDeclaration':
        for declaration in node.declarations:
          if declaration.init.type == 'CallExpression':
            func_type = self.expressionHelper(declaration.init)
            if func_type:
              self.features[func_type] += 1
              self.nodes.append(node)

    # Add conditionals for future learning goals here
    # TODO: Add list or file to store names of learning goals that are being statically assessed
    # Feature extraction for U3L11 'Position - Elements and the Coordinate System'
    if learning_goal["Key Concept"] == 'Position - Elements and the Coordinate System':
      esprima.parseScript(program, {'tolerant': True, 'comment': True, 'loc': True}, positionElementsAndTheCoordinateSystemDelegate)
      dt = DecisionTrees()
      self.assessment = dt.assess_position_elements(self.features)
