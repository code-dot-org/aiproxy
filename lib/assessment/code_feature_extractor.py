import esprima
from lib.assessment.decision_trees import DecisionTrees
import logging

class CodeFeatures:

  def __init__(self):
    self.code_features = {'shapes': 0, 'sprites': 0, 'text': 0}
    self.nodes = []
    self.assessment = ''

  # Feature extraction and labeling functions
    
  # Check number of arguments in an expression
  def argumentHelper(self, expression):
    return True if len(expression.arguments) >= 2 else False

  # Output the expression type
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

  def extract_code_features(self, program, learning_goal):

    # Delegate function to extract shape function call info from code and store it in shapesInfo
    def positionElementsAndTheCoordinateSystemDelegate(node, metadata):
      if node.type == 'ExpressionStatement' and node.expression.type == 'CallExpression':
        func_type = self.expressionHelper(node.expression)
        if func_type:
          self.code_features[func_type] += 1
          self.nodes.append(node)
      elif node.type == 'VariableDeclaration':
        for declaration in node.declarations:
          if declaration.init.type == 'CallExpression':
            func_type = self.expressionHelper(declaration.init)
            if func_type:
              self.code_features[func_type] += 1
              self.nodes.append(node)

    if learning_goal["Key Concept"] == 'Position - Elements and the Coordinate System':
      esprima.parseScript(program, {'tolerant': True, 'comment': True, 'loc': True}, positionElementsAndTheCoordinateSystemDelegate)
      dt = DecisionTrees()
      self.assessment = dt.assess_position_elements(self.code_features)
