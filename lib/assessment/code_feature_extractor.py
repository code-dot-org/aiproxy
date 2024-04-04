import esprima
from lib.assessment.decision_trees import DecisionTrees
import logging

function_args = {
    "arc": ["x", "y", "w", "h", "start", "stop"],
    "background": ["color"],
    "createSprite": ["x", "y", "w", "h"],
    "ellipse": ["x", "y", "w", "h"],
    "fill": ["color"],
    "line": ["x1", "y1", "x2", "y2"],
    "point": ["x", "y"],
    "rect": ["x", "y", "w", "h"],
    "regularPolygon": ["x", "y", "sides", "size"],
    "rgb": ["r", "g", "b", "a"],
    "shape": ["x1", "y1", "xn", "yn"],
    "text": ["str", "x", "y", "width", "height"]
}

shape_functions = ['circle',
                   'ellipse',
                   'quad',
                   'rect',
                   'regularPolygon',
                   'shape',
                   'triangle']

# This class contains delegate and helper functions to extract relevant features
# from code for assessment. New features should be added to the features dictionary.
# Add delegate function definitions to the extract_features function.
class CodeFeatures:

  def __init__(self):

    # Dictionary for storing features parsed from code sample
    self.features = {'object_types': {'shapes': 0, 'sprites': 0, 'text': 0},
                     'variables': [],
                     'objects': [],
                     'movement': {'random': 0, 'counter': 0}}

    # Store relevant parse tree nodes here during extraction. This will be useful
    # For returning metadata like line and column numbers or for exploring additional
    # info about the extracted features
    self.nodes = []

    # For learning goals that are assessed by decision tree and not the LLM, store the
    # assessment results here
    self.assessment = ''

  # Helper function for parsing binary expressions.
  # Outputs a dictionary containing both sides of the expression and the operator
  def binary_expression_helper(self, expression):
    output = []
    for exp in [expression.left, expression.right]:
      match exp.type:
        case "MemberExpression":
          output.append(self.member_expression_helper(exp))
        case "Identifier":
          output.append(exp.name)
        case "Literal":
          output.append(exp.value)
        case "CallExpression":
          output.append(self.call_expression_helper(exp))
        case "UnaryExpression":
          output.append(self.unary_expression_helper(exp))
        case _:
          logging.info("binary expression outlier", str(exp)) # DEBUG
    return {"left": output[0], "operator": expression.operator, "right": output[1]}

  # Helper function for parsing function calls. Outputs a dictionary containing the
  # function identifier and the arguments. Arguments are labeled with their respective
  # attributes for built-in functions (See function_args dict)
  def call_expression_helper(self, expression):
    # Get function / method identifier
    if expression.callee.type == "MemberExpression":
      function = {"object": expression.callee.object.name, "method": expression.callee.property.name}
    else:
      function = expression.callee.name

    # Get arguments
    args = {}
    arg_values = []
    for argument in expression.arguments:
      if argument.type == "Literal":
        arg_values.append(argument.value)
      elif argument.type == "Identifier":
        arg_values.append(argument.name)

    # Combine function / method identifier and arguments
    if expression.callee.type == "MemberExpression":
      args = arg_values
    else:
      if function in function_args:
        arg_names = function_args[function]
        for i, value in enumerate(arg_values):
          args[arg_names[i]] = [value]
      else:
        args = arg_values
    return {"function": function, "args": args}

  # Helper function to analyze all statements in the draw loop. Sends statements
  # to their respective helper functions for parsing based on statement type.
  # Returns a list of all statement outputs.
  def draw_loop_helper(self, node):
    if node.type == "FunctionDeclaration" and node.id.name == "draw":
      draw_loop_body = []
      for statement in node.body.body:
        match statement.type:
          case "ExpressionStatement":
            match statement.expression.type:
              case "CallExpression":
                draw_loop_body.append(self.call_expression_helper(statement.expression))
              case "AssignmentExpression":
                draw_loop_body.append(self.variable_assignment_helper(statement))
              case _:
                logging.info("draw loop outlier expression", str(statement.expression))
          case "VariableDeclaration":
            for declaration in self.variable_declaration_helper(statement):
              draw_loop_body.append(declaration)
          case "IfStatement":
            draw_loop_body.append(self.if_statement_helper(statement))
          case _:
            logging.info("draw loop outlier statement", str(statement))
      return draw_loop_body

  # Helper function to parse all statements in an if block
  def if_statement_helper(self, node):
    if node.type == "IfStatement":
      test = None
      match node.test.type:
        case "Identifier":
          test = node.test.name
        case "MemberExpression":
          test = self.member_expression_helper(node.test)
        case "Literal":
          test = node.test.value
        case "BinaryExpression":
          test = self.binary_expression_helper(node.test)
        case "CallExpression":
          test = self.call_expression_helper(node.test)
        case "UnaryExpression":
          test = self.unary_expression_helper(node.test)
        case _:
          logging.info("conditional test outlier", str(node.test))
      consequent = []
      for statement in node.consequent.body:
        match statement.type:
          case "ExpressionStatement":
            match statement.expression.type:
              case "CallExpression":
                consequent.append(self.call_expression_helper(statement.expression))
              case "AssignmentExpression":
                consequent.append(self.variable_assignment_helper(statement))
              case _:
                logging.info("conditional consequent outlier expression", str(statement.expression))
          case "VariableDeclaration":
            for declaration in self.variable_declaration_helper(statement):
              consequent.append(declaration)
          case "IfStatement":
            consequent.append(self.if_statement_helper(statement))
          case _:
            logging.info("conditional consequent outlier statement", str(statement))
      alternate = []
      if node.alternate and node.alternate.body:
        for statement in node.alternate.body:
          match statement.type:
            case "ExpressionStatement":
              match statement.expression.type:
                case "CallExpression":
                  alternate.append(self.call_expression_helper(statement.expression))
                case "AssignmentExpression":
                  alternate.append(self.variable_assignment_helper(statement))
                case _:
                  logging.info("conditional alternate outlier expression", str(statement.expression))
            case "VariableDeclaration":
              for declaration in self.variable_declaration_helper(statement):
                alternate.append(declaration)
            case "IfStatement":
              alternate.append(self.if_statement_helper(statement))
            case _:
              logging.info("conditional alternate outlier statement", str(statement))
      return {"test": test, "consequent": consequent, "alternate": alternate}

  # This function is used to extract statements from all conditional paths,
  # including nested conditionals, for analysis
  def flatten_conditional_paths(self, conditional):
    statements = conditional["consequent"]
    if "alternate" in conditional:
      statements.extend(conditional["alternate"])
    nested_conditionals = [statement for statement in statements if "test" in statement]
    if nested_conditionals:
      for cond in nested_conditionals:
       statements.extend(self.flatten_conditional_paths(cond))
    statements = [statement for statement in statements if "test" not in statement]
    return statements

  # Helper function to parse member expressions (i.e., an object and its property).
  # Returns a dict containing the object and the property being operated on.
  def member_expression_helper(self, expression):
    # Get object and property names
    if expression.object.type == "Identifier":
      member_expression = {"object": expression.object.name, "property": expression.property.name}
    else:
      logging.info("member expression outlier", str(expression)) # DEBUG
    return member_expression

  # Helper function to parse unary functions. Returns a float combining the
  # operator and number
  def unary_expression_helper(self, expression):
    if expression.argument.type == "Literal":
      return float(expression.operator + expression.argument.raw)
    else:
      logging.info("unary expression outlier", str(expression)) #DEBUG

  def variable_declaration_helper(self, node):
    declarations = []
    for declaration in node.declarations:
      identifier = declaration.id.name
      if declaration.init.type == "CallExpression":
        value = self.call_expression_helper(declaration.init)
      else:
        value = declaration.init.value
      declarations.append({"identifier": identifier, "value": value})
    return declarations

  # Helper function to parse variable assignment statements. Returns a dict
  # containing the assignee variable and the value to be assigned.
  def variable_assignment_helper(self, node):
    output = []
    for exp in [node.expression.left, node.expression.right]:
      match exp.type:
        case "Identifier":
          output.append(exp.name)
        case "MemberExpression":
          output.append(self.member_expression_helper(exp))
        case "Literal":
          output.append(exp.value)
        case "BinaryExpression":
          output.append(self.binary_expression_helper(exp))
        case "CallExpression":
          output.append(self.call_expression_helper(exp))
        case "UnaryExpression":
          output.append(self.unary_expression_helper(exp))
        case _:
          logging.info("variable assignment outlier", str(exp))
    return {"assignee": output[0], "value": output[1]}
  
  # Extractor functions: These functions utilize helper functions to return
  # information from nodes, then store the relevant code features in the
  # features dictionary.
  # Extract and store counter and random movement instances in features dictionary
  def extract_movement_types(self, node):
    draw_loop_info = self.draw_loop_helper(node)
    if draw_loop_info:
      for statement in draw_loop_info:
        if "assignee" in statement:
          if "object" in statement["assignee"]:
            obj = [obj for obj in self.features["objects"] if obj["identifier"] == statement["assignee"]["object"]]
            if obj:
              if isinstance(statement["value"], dict):
                if "left" in statement["value"]:
                  if statement["assignee"] in [statement["value"]["left"], statement["value"]["right"]]:
                    if statement["value"]["operator"] in ["+", "-"]:
                      self.features["movement"]["counter"] += 1
                      self.nodes.append(node)
                  if [stmnt for stmnt in [statement["value"]["left"], statement["value"]["right"]] if isinstance(stmnt, dict) and "function" in stmnt and "randomNumber" in stmnt["function"]]:
                    self.features["movement"]["random"] += 1
                    self.nodes.append(node)
                elif "function" in statement["value"] and statement["value"]["function"] == "randomNumber":
                    self.features["movement"]["random"] += 1
                    self.nodes.append(node)
        if "test" in statement:
          conditional_body = self.flatten_conditional_paths(statement)
          for conditional_statement in conditional_body:
            if "assignee" in conditional_statement:
              if "object" in conditional_statement["assignee"]:
                obj = [obj for obj in self.features["objects"] if obj["identifier"] == conditional_statement["assignee"]["object"]]
                if obj:
                  if isinstance(conditional_statement["value"], dict):
                    if "left" in conditional_statement["value"]:
                      if conditional_statement["assignee"] in [conditional_statement["value"]["left"], conditional_statement["value"]["right"]]:
                        if conditional_statement["value"]["operator"] in ["+", "-"]:
                          self.features["movement"]["counter"] += 1
                          self.nodes.append(node)
                      if [stmnt for stmnt in [conditional_statement["value"]["left"], conditional_statement["value"]["right"]] if isinstance(stmnt, dict) and "function" in stmnt and "randomNumber" in stmnt["function"]]:
                        self.features["movement"]["random"] += 1
                        self.nodes.append(node)
                    elif "function" in conditional_statement["value"] and conditional_statement["value"]["function"] == "randomNumber":
                        self.features["movement"]["random"] += 1
                        self.nodes.append(node)

  # Extract and store all object and variable data, including object types
  def extract_object_and_variable_data(self, node):
    if node.type == "VariableDeclaration":
      for node_info in self.variable_declaration_helper(node):
        if node_info["identifier"] not in [obj["identifier"] for obj in self.features["objects"]] and node_info["identifier"] not in [var["identifier"] for var in self.features["variables"]]:
          if isinstance(node_info["value"], dict) and "function" in node_info["value"]:
            if node_info["value"]["function"] == "createSprite":
              self.features["objects"].append({"identifier": node_info["identifier"], "properties": node_info["value"]["args"], "type": "sprite"})
              self.features["object_types"]["sprites"] += 1
              self.nodes.append(node)
            elif node_info["value"]["function"] == "text":
              self.features["objects"].append({"identifier": node_info["identifier"], "properties": node_info["value"]["args"], "type": "text"})
              self.features["object_types"]["text"] += 1
              self.nodes.append(node)
            elif node_info["value"]["function"] in shape_functions:
              self.features["objects"].append({"identifier": node_info["identifier"], "properties": node_info["value"]["args"], "type": "shape"})
              self.features["object_types"]["shapes"] += 1
              self.nodes.append(node)
          else:
            self.features["variables"].append({"identifier": node_info["identifier"], "value": node_info["value"]})
            self.nodes.append(node)
    elif node.type == "ExpressionStatement" and node.expression.type == "CallExpression":
      node_info = self.call_expression_helper(node.expression)
      if node_info["function"] == "background":
        self.features["objects"].append({"identifier": '', "properties": node_info["args"], "type": "background"})
        self.nodes.append(node)
      elif node_info["function"] == "text":
        self.features["objects"].append({"identifier": '', "properties": node_info["args"], "type": "text"})
        self.features["object_types"]["text"] += 1
        self.nodes.append(node)
      elif node_info["function"] in shape_functions:
        self.features["objects"].append({"identifier": '', "properties": node_info["args"], "type": "shape"})
        self.features["object_types"]["shapes"] += 1
        self.nodes.append(node)

  # Function to extract features for learning goals. Contains delegate functions
  # to be used with the parser. Does not return any values, but should populate
  # the features dictionary with values based on parse results
  def extract_features(self, program, learning_goal, lesson):

    # Function to parse code using esprima. If the code reaches an error state that
    # esprima cannot handle, it will be logged, and parsing will continue from
    # the next line of code.
    def parse_code(program, delegate):
      try:
        parsed = esprima.parseScript(program, {'tolerant': True, 'comment': True, 'loc': True}, u3l18_position_delegate)
      except Exception as e:
        err = str(e)
        if "Line" in err:
          logging.error(err)
          line_num = int(err.replace("Line ", "").split(":")[0])
          program_slice = '\n'.join(program.split('\n')[line_num:])
          parse_code(program_slice, delegate)
        else:
          logging.error("Parsing error", err)

    # Delegate function for U3L11 'Position - Elements and the Coordinate System'
    def u3l11_position_delegate(node, metadata):
      # extract_object_types(node)
      self.extract_object_and_variable_data(node)

    # Delegate function for U3L14 'Position and Movement'
    def u3l14_position_delegate(node, metadata):
      # extract_object_types(node)
      self.extract_object_and_variable_data(node)
      self.extract_movement_types(node)

    # Delegate function for U3L18 'Position and Movement'
    def u3l18_position_delegate(node, metadata):
      # extract_object_types(node)
      self.extract_object_and_variable_data(node)
      self.extract_movement_types(node)

    # Add conditionals for future learning goals here
    # TODO: Add list or file to store names of learning goals that are being statically assessed
    match [learning_goal["Key Concept"], lesson]:
      case ['Position - Elements and the Coordinate System', 'csd3-2023-L11']:
        parse_code(program, u3l11_position_delegate)
        dt = DecisionTrees()
        self.assessment = dt.u3l11_position_assessment(self.features)
      case ['Position and Movement', 'csd3-2023-L14']:
        parse_code(program, u3l14_position_delegate)
        dt = DecisionTrees()
        self.assessment = dt.u3l14_position_assessment(self.features)
      case ['Position and Movement', 'csd3-2023-L18']:
        parse_code(program, u3l18_position_delegate)
        dt = DecisionTrees()
        self.assessment = dt.u3l18_position_assessment(self.features)
