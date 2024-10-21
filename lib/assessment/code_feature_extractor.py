import esprima
import logging

# Lists of arguments for object creation functions
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
    "text": ["str", "x", "y", "width", "height"]
}

# List of functions that draw a shape to the screen
shape_functions = ['circle',
                   'ellipse',
                   'quad',
                   'rect',
                   'regularPolygon',
                   'shape',
                   'triangle']

# List of sprite object functions
sprite_functions = ['setAnimation']

# List of object properties that are used for movement
obj_movement_props = ['x', 'y', 'velocityX', 'velocityY', 'rotation']

# List of functions that allow user interaction
user_interaction_functions = ['keyDown', 
                              'keyWentDown', 
                              'keyWentUp', 
                              'mouseDidMove', 
                              'mouseDown', 
                              'mouseIsOver', 
                              'mousePressedOver', 
                              'mouseWentDown', 
                              'mouseWentUp']

# This class contains delegate and helper functions to extract relevant features
# from code for assessment. New features should be added to the features dictionary.
# Add delegate function definitions to the extract_features function.
class CodeFeatures:

  def __init__(self):

    # Dictionary for storing features parsed from code sample
    self.features = {'conditionals': [],
                     'draw_loop': {},
                     'movement': {'random': {'count': 0, 'lines': []}, 'counter': {'count':0, 'lines': []}},
                     'objects': [],
                     'object_types': {'shapes': 0, 'sprites': 0, 'text': 0},
                     'property_change': [],
                     'user_functions': [],
                     'function_calls': [],
                     'variables': [],}

    # Store relevant parse tree nodes here during extraction. This will be useful
    # For returning metadata like line and column numbers or for exploring additional
    # info about the extracted features
    self.nodes = []

  # Helper function for parsing binary expressions.
  # Outputs a dictionary containing both sides of the expression and the operator
  def binary_expression_helper(self, expression):
    output = []
    for exp in [expression.left, expression.right]:
      match exp.type:
        case "MemberExpression":
          output.append(self.member_expression_helper(exp))
        case "Identifier":
          output.append({'identifier': exp.name})
        case "Literal":
          output.append({'literal': exp.value})
        case "CallExpression":
          output.append(self.call_expression_helper(exp))
        case "UnaryExpression":
          output.append(self.unary_expression_helper(exp))
        case _:
          logging.debug(f"binary expression outlier: {exp}") # DEBUG
    return {"left": output[0], "operator": expression.operator, "right": output[1], "start": expression.loc.start.line, "end": expression.loc.end.line}

  # Helper function for parsing function calls. Outputs a dictionary containing the
  # function identifier and the arguments. Arguments are labeled with their respective
  # attributes for built-in functions (See function_args dict)
  def call_expression_helper(self, expression):
    # Get function / method identifier
    if expression.callee.type == "MemberExpression":
      called_func = {"object": expression.callee.object.name, "method": expression.callee.property.name, "start": expression.loc.start.line, "end": expression.loc.end.line}
    else:
      called_func = expression.callee.name
    
    if called_func in user_interaction_functions:
      user_interaction = True
    else:
      user_interaction = False

    # Get arguments
    args = {}
    arg_values = []
    for argument in expression.arguments:
      if argument.type == "Literal":
        arg_values.append(argument.value)
      elif argument.type == "Identifier":
        arg_values.append(argument.name)
      elif argument.type == "CallExpression":
        arg_values.append(self.call_expression_helper(argument))

    # Combine function / method identifier and arguments
    if expression.callee.type == "MemberExpression":
      args = arg_values
    else:
      if called_func in function_args:
        arg_names = function_args[called_func]
        for i, value in enumerate(arg_values):
          args[arg_names[i]] = [value]
      else:
        args = arg_values
    return {"function": called_func, "args": args, 'user_interaction': user_interaction, "start": expression.loc.start.line, "end": expression.loc.end.line}
      
  # Helper function to analyze all statements in the draw loop. Sends statements
  # to their respective helper functions for parsing based on statement type.
  # Returns a list of all statement outputs.
  def draw_loop_helper(self, node):
    if node.type == "FunctionDeclaration" and node.id.name == "draw":
      self.features['draw_loop']['start'] = node.loc.start.line
      self.features['draw_loop']['end'] = node.loc.end.line
      draw_loop_body = []
      for statement in node.body.body:
        match statement.type:
          case "ExpressionStatement":
            match statement.expression.type:
              case "CallExpression":
                draw_loop_body.append(self.call_expression_helper(statement.expression))
              case "AssignmentExpression":
                draw_loop_body.append(self.variable_assignment_helper(statement))
              case "UpdateExpression":
                draw_loop_body.append(self.update_expression_helper(statement.expression))
              case _:
                logging.debug(f"draw loop outlier expression: {statement.expression}")
          case "VariableDeclaration":
            for declaration in self.variable_declaration_helper(statement):
              draw_loop_body.append(declaration)
          case "IfStatement":
            draw_loop_body.append(self.if_statement_helper(statement))
          case "FunctionDeclaration":
            draw_loop_body.append(self.function_def_helper(statement))
          case _:
            logging.debug(f"draw loop outlier statement: {statement}")
      return draw_loop_body

  def function_def_helper(self, node):
    if node.type == "FunctionDeclaration" and node.id.name != "draw":
      start = node.loc.start.line
      end = node.loc.end.line
      function_body = []
      for statement in node.body.body:
        match statement.type:
          case "ExpressionStatement":
            match statement.expression.type:
              case "CallExpression":
                function_body.append(self.call_expression_helper(statement.expression))
              case "AssignmentExpression":
                function_body.append(self.variable_assignment_helper(statement))
              case "UpdateExpression":
                function_body.append(self.update_expression_helper(statement.expression))
              case _:
                logging.debug(f"draw loop outlier expression: {statement.expression}")
          case "VariableDeclaration":
            for declaration in self.variable_declaration_helper(statement):
              function_body.append(declaration)
          case "IfStatement":
            function_body.append(self.if_statement_helper(statement))
          case "FunctionDeclaration":
            function_body.append(self.function_def_helper(statement))
          case _:
            logging.debug(f"draw loop outlier statement: {statement}")
      return {"function": node.id.name, "body": function_body, "start": start, "end": end, "calls": 0}

  # Helper function to parse all statements in an if block
  def if_statement_helper(self, node):
    if node.type == "IfStatement":
      test = {}
      match node.test.type:
        case "Identifier":
          test = {'identifier': node.test.name}
        case "MemberExpression":
          test = self.member_expression_helper(node.test)
        case "Literal":
          test = {'literal': node.test.value}
        case "BinaryExpression":
          test = self.binary_expression_helper(node.test)
        case "CallExpression":
          test = self.call_expression_helper(node.test)
        case "UnaryExpression":
          test = self.unary_expression_helper(node.test)
        case _:
          logging.debug(f"conditional test outlier: {node.test}")
      consequent = []
      for statement in node.consequent.body:
        match statement.type:
          case "ExpressionStatement":
            match statement.expression.type:
              case "CallExpression":
                consequent.append(self.call_expression_helper(statement.expression))
              case "AssignmentExpression":
                consequent.append(self.variable_assignment_helper(statement))
              case "UpdateExpression":
                consequent.append(self.update_expression_helper(statement.expression))
              case _:
                logging.debug(f"conditional consequent outlier expression: {statement.expression}")
          case "VariableDeclaration":
            for declaration in self.variable_declaration_helper(statement):
              consequent.append(declaration)
          case "IfStatement":
            consequent.append(self.if_statement_helper(statement))
          case "FunctionDeclaration":
            consequent.append(self.function_def_helper(statement))
          case _:
            logging.debug(f"conditional consequent outlier statement: {statement}")
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
                case "UpdateExpression":
                  alternate.append(self.update_expression_helper(statement.expression))
                case _:
                  logging.debug(f"conditional alternate outlier expression: {statement.expression}")
            case "VariableDeclaration":
              for declaration in self.variable_declaration_helper(statement):
                alternate.append(declaration)
            case "IfStatement":
              alternate.append(self.if_statement_helper(statement))
            case "FunctionDeclaration":
              alternate.append(self.function_def_helper(statement))
            case _:
              logging.debug(f"conditional alternate outlier statement: {statement}")
      return {"test": test, "consequent": consequent, "alternate": alternate, "start": node.loc.start.line, "end": node.loc.end.line}

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
    member_expression = {}
    if expression.object.type == "Identifier":
      member_expression = {"object": expression.object.name, "property": expression.property.name, "start": expression.loc.start.line, "end": expression.loc.end.line}
    else:
      logging.debug(f"member expression outlier: {expression}") # DEBUG
    return member_expression

  # Helper function to parse unary functions. Returns a float combining the
  # operator and number
  def unary_expression_helper(self, expression):
    if expression.argument.type == "Literal":
      return float(expression.operator + expression.argument.raw)
    else:
      logging.debug(f"unary expression outlier: {expression}") #DEBUG

  def update_expression_helper(self, expression):
    argument = {}
    match expression.argument.type:
      case "MemberExpression":
        argument = self.member_expression_helper(expression.argument)
      case "Identifier":
        argument = expression.argument.name
      case _:
        logging.debug(f"update expression argument outlier: {expression.argument}")
    return {"operator":expression.operator, "argument":argument, "start": expression.loc.start.line, "end": expression.loc.end.line}

  def variable_declaration_helper(self, node):
    declarations = []
    for declaration in node.declarations:
      identifier = declaration.id.name
      if declaration.init.type == "CallExpression":
        value = self.call_expression_helper(declaration.init)
      else:
        value = declaration.init.value
      declarations.append({"identifier": identifier, "value": value, "start": node.loc.start.line, "end": node.loc.end.line})
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
          logging.debug(f"variable assignment outlier: {exp}")
    return {"assignee": output[0], "value": output[1], "start": node.loc.start.line, "end": node.loc.end.line}
  
  # Extractor functions: These functions utilize helper functions to return
  # information from nodes, then store the relevant code features in the
  # features dictionary.

  # Extract and store data about conditional test statements
  def extract_conditionals(self, node):
    # If node is the draw loop, make sure that all conditionals within the draw loop are flagged
    draw_loop = self.draw_loop_helper(node)
    if draw_loop:
      for i, statement in enumerate(self.features['conditionals']):
        if 'start' in statement and statement['start'] >= self.features['draw_loop']['start'] and statement['end'] <= self.features['draw_loop']['end']:
          self.features['conditionals'][i]['draw_loop'] = True

    # If node is a conditional, parse position and trigger information and save the test to features
    conditional = self.if_statement_helper(node)
    if conditional:
      if 'start' in self.features['draw_loop'].keys() and conditional['start'] >= self.features['draw_loop']['start'] and conditional['end'] <= self.features['draw_loop']['end']:
        conditional_info = {**conditional, 'draw_loop': True}
      else:
        conditional_info = {**conditional, 'draw_loop': False}
      
      # If conditional test is a binary expression, check both sides for trigger
      if 'left' in conditional_info["test"]:
        if (type(conditional_info["test"]['left']) == dict and 'identifier' in conditional_info["test"]["left"].keys()) or (type(conditional_info["test"]['right']) == dict and 'identifier' in conditional_info["test"]['right'].keys()):
          conditional_info = {**conditional_info, 'trigger': 'variable'}
        elif (type(conditional_info["test"]['left']) == dict and 'object' in conditional_info["test"]["left"].keys()) or (type(conditional_info["test"]['right']) == dict and 'object' in conditional_info["test"]['right'].keys()):
          conditional_info = {**conditional_info, 'trigger': 'object'}
        elif (type(conditional_info["test"]['left']) == dict and 'user_interaction' in conditional_info["test"]["left"].keys()) or (type(conditional_info["test"]['right']) == dict and 'user_interaction' in conditional_info["test"]['right'].keys()):
          conditional_info = {**conditional_info, 'trigger': 'user'}
      elif 'user_interaction' in conditional_info["test"]:
        conditional_info = {**conditional_info, 'trigger': 'user'}
      elif 'object' in conditional_info["test"]:
        conditional_info = {**conditional_info, 'trigger': 'object'}
      elif 'identifier' in conditional_info["test"]:
        conditional_info = {**conditional_info, 'trigger': 'variable'}
      else:
        conditional_info = {**conditional_info, 'trigger': 'untracked'}
      self.features['conditionals'].append(conditional_info)
      self.nodes.append(node)

  # Extract and store information about user defined functions 
  def extract_function_definitions(self, node):
    func_def = self.function_def_helper(node)
    if func_def:
      if func_def['function'] in [call['function'] for call in self.features['function_calls']]:
        func_def['calls'] += len([call for call in self.features['function_calls'] if call['function'] == func_def['function']])
      if "start" in self.features["draw_loop"] and (func_def["start"] >= self.features["draw_loop"]["start"] and func_def["start"] <= self.features["draw_loop"]["end"]):
        func_def['draw_loop'] = True
      self.features['user_functions'].append(func_def)
      self.nodes.append(node)

  def extract_function_calls(self, node):
    if node.type == "ExpressionStatement" and node.expression.type == "CallExpression":
      call = self.call_expression_helper(node.expression)
      self.features['function_calls'].append(call)
      self.nodes.append(node)

      if len(self.features['user_functions']) > 0 and call['function'] in [func['function'] for func in self.features['user_functions']]:
        i = [index for (index, func) in enumerate(self.features['user_functions']) if func['function'] == call['function']][0]
        self.features['user_functions'][i]['calls'] += 1
        self.nodes.append(node)

  # Extract and store counter and random movement instances in features dictionary
  def extract_movement_types(self, node):
    draw_loop_info = self.draw_loop_helper(node)
    if draw_loop_info:
      for statement in draw_loop_info:
        if "assignee" in statement:
          if "object" in statement["assignee"] and "property" in statement["assignee"] and statement["assignee"]["property"] in obj_movement_props:
            obj = [obj for obj in self.features["objects"] if obj["identifier"] == statement["assignee"]["object"]]
            if obj:
              if isinstance(statement["value"], dict):
                if "left" in statement["value"]:
                  if statement["assignee"] in [statement["value"]["left"], statement["value"]["right"]] and statement["value"]["operator"] in ["+", "-"]:
                    self.features["movement"]["counter"]["count"] += 1
                    self.features["movement"]["counter"]["lines"].append({'start': statement["start"], 'end': statement["end"]})
                    self.nodes.append(node)
                  if [stmnt for stmnt in [statement["value"]["left"], statement["value"]["right"]] if isinstance(stmnt, dict) and "function" in stmnt and "randomNumber" in stmnt["function"]]:
                    self.features["movement"]["random"]["count"] += 1
                    self.features["movement"]["random"]["lines"].append({'start': statement["start"], 'end': statement["end"]})
                    self.nodes.append(node)
                elif "function" in statement["value"] and statement["value"]["function"] == "randomNumber":
                    self.features["movement"]["random"]["count"] += 1
                    self.features["movement"]["random"]["lines"].append({'start': statement["start"], 'end': statement["end"]})
                    self.nodes.append(node)
        if "operator" in statement and statement["operator"] in ["++", "--"]:
          if "object" in statement["argument"] and "property" in statement["argument"] and statement["argument"]["property"] in obj_movement_props:
            obj = [obj for obj in self.features["objects"] if obj["identifier"] == statement["argument"]["object"]]
            if obj:
              self.features["movement"]["counter"]["count"] += 1
              self.features["movement"]["counter"]["lines"].append({'start': statement["start"], 'end': statement["end"]})
              self.nodes.append(node)
        if "test" in statement:
          conditional_body = self.flatten_conditional_paths(statement)
          for conditional_statement in conditional_body:
            if "operator" in conditional_statement and conditional_statement["operator"] in ["++", "--"]:
              if "object" in conditional_statement["argument"] and "property" in conditional_statement["argument"] and conditional_statement["argument"]["property"] in obj_movement_props:
                obj = [obj for obj in self.features["objects"] if obj["identifier"] == conditional_statement["argument"]["object"]]
                if obj:
                  self.features["movement"]["counter"]["count"] += 1
                  self.features["movement"]["counter"]["lines"].append({'start': statement["start"], 'end': statement["end"]})
                  self.nodes.append(node)
            if "assignee" in conditional_statement:
              if "object" in conditional_statement["assignee"] and "property" in conditional_statement["assignee"] and conditional_statement["assignee"]["property"] in obj_movement_props:
                obj = [obj for obj in self.features["objects"] if obj["identifier"] == conditional_statement["assignee"]["object"]]
                if obj:
                  if isinstance(conditional_statement["value"], dict):
                    if "left" in conditional_statement["value"]:
                      if conditional_statement["assignee"] in [conditional_statement["value"]["left"], conditional_statement["value"]["right"]]:
                        if conditional_statement["value"]["operator"] in ["+", "-"]:
                          self.features["movement"]["counter"]["count"] += 1
                          self.features["movement"]["counter"]["lines"].append({'start': statement["start"], 'end': statement["end"]})
                          self.nodes.append(node)
                      if [stmnt for stmnt in [conditional_statement["value"]["left"], conditional_statement["value"]["right"]] if isinstance(stmnt, dict) and "function" in stmnt and "randomNumber" in stmnt["function"]]:
                        self.features["movement"]["random"]["count"] += 1
                        self.features["movement"]["random"]["lines"].append({'start': statement["start"], 'end': statement["end"]})
                        self.nodes.append(node)
                    elif "function" in conditional_statement["value"] and conditional_statement["value"]["function"] == "randomNumber":
                        self.features["movement"]["random"]["count"] += 1
                        self.features["movement"]["random"]["lines"].append({'start': statement["start"], 'end': statement["end"]})
                        self.nodes.append(node)

  # Extract and store all object and variable data, including object types
  def extract_object_and_variable_data(self, node):
    if node.type == "VariableDeclaration":
      for node_info in self.variable_declaration_helper(node):
        if node_info["identifier"] not in [obj["identifier"] for obj in self.features["objects"]] and node_info["identifier"] not in [var["identifier"] for var in self.features["variables"]]:
          if isinstance(node_info["value"], dict) and "function" in node_info["value"]:
            if node_info["value"]["function"] == "createSprite":
              self.features["objects"].append({"identifier": node_info["identifier"], "properties": node_info["value"]["args"], "type": "sprite", "start": node_info["start"], "end": node_info["end"]})
              self.features["object_types"]["sprites"] += 1
              self.nodes.append(node)
            elif node_info["value"]["function"] == "text":
              self.features["objects"].append({"identifier": node_info["identifier"], "properties": node_info["value"]["args"], "type": "text", "start": node_info["start"], "end": node_info["end"]})
              self.features["object_types"]["text"] += 1
              self.nodes.append(node)
            elif node_info["value"]["function"] in shape_functions:
              self.features["objects"].append({"identifier": node_info["identifier"], "properties": node_info["value"]["args"], "type": "shape", "start": node_info["start"], "end": node_info["end"]})
              self.features["object_types"]["shapes"] += 1
              self.nodes.append(node)
            else:
              self.features["variables"].append({"identifier": node_info["identifier"], "properties": node_info["value"]["args"], "type": "none", "start": node_info["start"], "end": node_info["end"]})
              self.nodes.append(node)
          else:
            self.features["variables"].append({"identifier": node_info["identifier"], "value": node_info["value"], "start": node_info["start"], "end": node_info["end"]})
            self.nodes.append(node)
    elif node.type == "ExpressionStatement" and node.expression.type == "CallExpression":
      node_info = self.call_expression_helper(node.expression)
      if node_info["function"] == "background":
        self.features["objects"].append({"identifier": '', "properties": node_info["args"], "type": "background", "start": node_info["start"], "end": node_info["end"]})
        self.nodes.append(node)
      elif node_info["function"] == "text":
        self.features["objects"].append({"identifier": '', "properties": node_info["args"], "type": "text", "start": node_info["start"], "end": node_info["end"]})
        self.features["object_types"]["text"] += 1
        self.nodes.append(node)
      elif node_info["function"] in shape_functions:
        self.features["objects"].append({"identifier": '', "properties": node_info["args"], "type": "shape", "start": node_info["start"], "end": node_info["end"]})
        self.features["object_types"]["shapes"] += 1
        self.nodes.append(node)

  #Extract and store all object properties that are updated
  def extract_property_assignment(self, node):
    draw_loop = self.draw_loop_helper(node)
    if draw_loop:
      # For any properties that change in the drawloop, change "draw_loop" to true
      new_properties = []
      for property in self.features["property_change"]:
        if property["start"] >= self.features['draw_loop']['start'] and property["end"] <= self.features['draw_loop']['end']:
          property["draw_loop"] = True
        new_properties.append(property)
      self.features["property_change"] = new_properties
      self.nodes.append(node)
    elif node.type == "ExpressionStatement" and node.expression.type == "CallExpression":
      node_info = self.call_expression_helper(node.expression)
      if type(node_info["function"]) is dict and all([k in node_info["function"].keys() for k in ["object", "method"]]) and node_info["function"]["method"] in sprite_functions:
        self.features["property_change"].append({**node_info["function"], "draw_loop":False})
        self.nodes.append(node)
    elif node.type == "ExpressionStatement" and node.expression.type == "AssignmentExpression":
      node_info = self.variable_assignment_helper(node)
      if type(node_info["assignee"]) is dict and all([k in node_info["assignee"].keys() for k in ["object", "property"]]):
        self.features["property_change"].append({**node_info["assignee"], "draw_loop":False})
        self.nodes.append(node)
    elif node.type == "ExpressionStatement" and node.expression.type == "UpdateExpression":
      node_info = self.update_expression_helper(node.expression)
      if type(node_info["argument"]) is dict and node_info["operator"] in ["++", "--", "~"] and all([k in node_info["argument"].keys() for k in ["object", "property"]]):
        self.features["property_change"].append({**node_info["argument"], "draw_loop":False})
        self.nodes.append(node)

  # Function to extract features for learning goals. Contains delegate functions
  # to be used with the parser. Does not return any values, but should populate
  # the features dictionary with values based on parse results
  def extract_features(self, program):

    # Function to parse code using esprima. If the code reaches an error state that
    # esprima cannot handle, it will be logged, and parsing will continue from
    # the next line of code.
    def parse_code(program):
      try:
        parsed = esprima.parseScript(program, {'tolerant': True, 'comment': True, 'loc': True}, delegate)
      except Exception as e:
        err = str(e)
        if "Line" in err:
          logging.error(err)
          line_num = int(err.replace("Line ", "").split(":")[0])
          program_slice = '\n'.join(program.split('\n')[line_num:])
          parse_code(program_slice)
        else:
          logging.error(f"Parsing error: {err}")

    # Delegate function to run feature extractors during code parsing
    def delegate(node, metadata):
      self.extract_object_and_variable_data(node)
      self.extract_movement_types(node)
      self.extract_property_assignment(node)
      self.extract_conditionals(node)
      self.extract_function_definitions(node)
      self.extract_function_calls(node)

    parse_code(program)
