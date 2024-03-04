import esprima
from lib.assessment.decision_trees import DecisionTrees
import logging

'''
This class contains delegate and helper functions to extract relevant features from code for assessment. 
New features should be added to the features dictionary.
Add delegate function definitions to the extract_features function.
'''
class CodeFeatures:

  def __init__(self):

    # Add additional features here
    self.features = {'shapes': 0, 'sprites': 0, 'text': 0}

    # Store relevant parse tree nodes here during extraction. This will be useful
    # For returning metadata like line and column numbers or for exploring additional
    # info about the extracted features
    self.nodes = []

    # For learning goals that are assessed by decision tree and not the LLM, store the
    # assessment results here
    self.assessment = ''

  # Feature extraction and labeling helper functions
    
  # Helper function to check number of arguments in an expression
  # Can be modified to provide additional info about arguments
  def argument_helper(self, expression):
    return True if len(expression.arguments) >= 2 else False

  # Helper function to identify and count all function calls in a program
  def function_call_helper(self, node):
    if node.type == 'ExpressionStatement' and node.expression.type == 'CallExpression':
      if node.expression.callee.name in self.features.keys():
        self.features[node.expression.callee.name] += 1
      else:
        self.features[node.expression.callee.name] = 1
    elif node.type == 'VariableDeclaration':
      for declaration in node.declarations:
        if declaration.init.type == 'CallExpression':
          if node.expression.callee.name in self.features.keys():
            self.features[node.expression.callee.name] += 1
          else:
            self.features[node.expression.callee.name] = 1

  # Helper function that returns the type of a called expression
  def expression_type_helper(self, expression):
    shapes = ['rect', 'ellipse', 'circle', 'quad', 'triangle']
    if expression.callee.name in shapes and self.argument_helper(expression):
      return 'shapes'
    elif expression.callee.name == 'text' and self.argument_helper(expression):
      return 'text'
    elif expression.callee.name == 'createSprite' and self.argument_helper(expression):
      return 'sprites'
    else:
      return None

  # All delegate functions and code feature extraction 
  def extract_features(self, program, learning_goal):

    # Delegate function for U3L11 'Position - Elements and the Coordinate System'
    # Add additional delegate functions here
    def u3l11_position(node, metadata):
      if node.type == 'ExpressionStatement' and node.expression.type == 'CallExpression':
        func_type = self.expression_type_helper(node.expression)
        if func_type:
          self.features[func_type] += 1
          self.nodes.append(node)
      elif node.type == 'VariableDeclaration':
        for declaration in node.declarations:
          if declaration.init.type == 'CallExpression':
            func_type = self.expression_type_helper(declaration.init)
            if func_type:
              self.features[func_type] += 1
              self.nodes.append(node)

    # Add conditionals for future learning goals here
    # TODO: Add list or file to store names of learning goals that are being statically assessed
    # Feature extraction for U3L11 'Position - Elements and the Coordinate System'
    if learning_goal["Key Concept"] == 'Position - Elements and the Coordinate System':
      esprima.parseScript(program, {'tolerant': True, 'comment': True, 'loc': True}, u3l11_position)
      dt = DecisionTrees()
      self.assessment = dt.u3l11_position_assessment(self.features)
