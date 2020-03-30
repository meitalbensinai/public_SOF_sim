__author__ = 'Meital'
# the visitor that is used in order to extract the data flow of python code - final outcome is the type ssignature
import ast
import networkx as nx
from pymongo import MongoClient

#some consts
client = MongoClient()
PY_DB = client.python
DB_TYPES_PARAM = PY_DB.func_to_types_new
TYPE_VARIABLE = "VAR"
TYPE_UNKNOWN = "Unknown"
TYPE_NUM = "Number"
TYPE_STR = "String"
TYPE_LIST = "List"
TYPE_TUPLE = "Tuple"
TYPE_DICT = "Dict"
TYPE_FUNC = "Func"
TYPE_PRINT = "Print"
TYPE_BOOL = "Boolean"
TYPE_RETURN = "Return"
TYPE_ITER = "Iterable"
TYPE_CONDITION = "Cond"
BOOLS = ["True", "False"]
LAST_LINE = "LAST()"
FROM_AST_TYPE = {ast.Str: TYPE_STR, ast.Dict: TYPE_DICT, ast.Num: TYPE_NUM, ast.List: TYPE_LIST,
                 ast.Tuple: TYPE_TUPLE}


class AnalysisNodeVisitor(ast.NodeVisitor):
    """the ast visiotr class"""
    def __init__(self, root_node=None):
        self._modules = []
        self._classes = []
        self._functions = {}
        self._imports = []
        self._rootNode = root_node
        self._parentNodes = [root_node]
        self._level = 0

        # the variabels that will be affected from the soon to come expressions
        self._affected_var = []

        self._curr_value = []
        self._look_for_vals = True
        self._look_for_names_only = False
        self._declared_inputs = []

        # last changed line, in case there is no return or print in the code
        self._last_changed = None
        self._inner_iter = []

        self._returns = []
        self._prints = []

        # Graph:
        self._graph = nx.DiGraph()

        #real types
        self._types = {}

    # properties getters
    @property
    def inner_iter(self):
        return self._inner_iter

    @property
    def graph(self):
        return self._graph

    @property
    def inputs(self):
        return self._declared_inputs

    @property
    def root_node(self):
        return self._rootNode

    @property
    def last_changed(self):
        return self._last_changed

    @property
    def literals_dep(self):
        return self._literals_dep

    @property
    def vars_dep(self):
        return self._vars_dep

    @property
    def types(self):
        return self._types

    @property
    def imports(self):
        return self._imports

    @property
    def functions(self):
        return self._functions

    @property
    def classes(self):
        return self._classes

    # visit functions
    def visit_Module(self, node):
        print ast.dump(node)
        ast.NodeVisitor.generic_visit(self, node)

    def visit_Import(self, node):
        self._imports += (map(lambda x: (x.name, None), node.names))
        ast.NodeVisitor.generic_visit(self, node)

    def visit_ImportFrom(self, node):
        mod = node.module
        self._imports += (map(lambda x: (x.name, mod), node.names))
        ast.NodeVisitor.generic_visit(self, node)

    def visit_Assign(self, node):
        try:
            names = node.targets[0].elts
        except:
            try:
                names = [node.targets[0]]
            except:
                names = []
        for name in names:
            self._curr_value = []
            try:
                name_id = name.id
            except:
                name_id = name.__dict__['value'].id
            self._affected_var = [(name_id, TYPE_VARIABLE)] + self._affected_var
            self._parentNodes = [node] + self._parentNodes
            ast.NodeVisitor.generic_visit(self, node)
            self._parentNodes = self._parentNodes[1:]
            self._affected_var = self._affected_var[1:]
            if len(self._curr_value) >= 1:
                self._types[self._get_node_name(name_id, TYPE_VARIABLE)] = self._curr_value[0]

    def visit_ListComp(self, node):
        try:
            self._inner_iter.append(self._get_node_name(node.__dict__['generators'][0].__dict__["target"].id, TYPE_VARIABLE))
        except:
            pass
        try:
            name = self._get_node_name(node.generators[0].iter.id, TYPE_VARIABLE)
            self._types[name] = self._types.get(name, TYPE_ITER)
        except:
            pass
        self._curr_value += [TYPE_LIST]
        if len(self._affected_var) == 0:
            self._last_changed = TYPE_RETURN + "()"
            self._types[TYPE_RETURN+"()"] = TYPE_LIST
            self._curr_value = []
            self._affected_var = [("", TYPE_RETURN)]
            self._parentNodes = [node] + self._parentNodes
            ast.NodeVisitor.generic_visit(self, node)
            self._parentNodes = self._parentNodes[1:]
            self._affected_var = self._affected_var[1:]
        else:
            ast.NodeVisitor.generic_visit(self, node)


    def visit_BinOp(self, node):
        ast.NodeVisitor.generic_visit(self, node)
        if len(self._curr_value) == 0:
            return
        first = None
        #print self._curr_value
        for val in self._curr_value:
            if first == None:
                first = val
            elif not val == first:
                self._curr_value = []
                return
        self._curr_value = [self._curr_value[0]]

    def visit_BoolOp(self, node):
        self._curr_value = [TYPE_BOOL]

    def visit_Attribute(self, node):
        self._parentNodes = [node] + self._parentNodes
        ast.NodeVisitor.generic_visit(self, node)
        self._parentNodes = self._parentNodes[1:]

    def visit_Name(self, node):
        if node.id in BOOLS or node.id in [e[0] for e in self.imports]:
            return
        _type = TYPE_VARIABLE
        if '_ast.Call' in str(type(self._parentNodes[0])) and self._parentNodes[0].func is node:
            _type = TYPE_FUNC
        self._graph.add_node(self._get_node_name(node.id, _type), type=_type)

        if '_ast.Attribute' in str(type(self._parentNodes[0])) and len(self._affected_var) == 1 and self._affected_var[0][1] == TYPE_FUNC:
            return

        if len(self._affected_var) > 0 and "Load" in str(node.ctx) and not(self._affected_var[0][0] == node.id):
            self._save_dependency(node.id, _type)

    def visit_List(self, node):
        # TODO: get inside?
        self._save_dependency(map(lambda x: ast.dump(x), node.elts), TYPE_LIST)

    def visit_Tuple(self, node):
        # TODO: get inside?
        store = True
        for op in node.elts:
            if "Load" in str(op.ctx):
                store = False
                break
        if store:
            ast.NodeVisitor.generic_visit(self, node)
        else:
            self._save_dependency(map(lambda x: ast.dump(x), node.elts), TYPE_TUPLE)

    def visit_Num(self, node):
        self._save_dependency(node.n, TYPE_NUM)

    def visit_Str(self, node):
        self._save_dependency(node.s, TYPE_STR)

    def _get_node_name(self, value, _type):
        """return the str representation of a value: _type(value)"""
        return "%s(%s)" % (_type, value)

    def _save_dependency(self, value, _type, name=None):
        """save the nodes and edges of the new value discovered"""
        print "!!!", self._affected_var, value, _type, name
        if name is None:
            name = _type
        if self._look_for_names_only and not _type == TYPE_VARIABLE:
            return
        name = self._get_node_name(value, name)
        if not _type == TYPE_VARIABLE and not _type == TYPE_FUNC:
            self._types[name] = _type
        self._graph.add_node(name, type=_type)
        if len(self._affected_var) > 0:
            self._graph.add_edges_from([(name, self._get_node_name(self._affected_var[0][0], self._affected_var[0][1]))])
            temp_type = self._types.get(name, _type)
            self._last_changed = self._affected_var[0][0]
            if self._look_for_vals and not temp_type == TYPE_FUNC:
                self._curr_value += [temp_type]

    def visit_Dict(self, node):
        # TODO: get inside?
        self._save_dependency(map(lambda x: ast.dump(x), node.values), TYPE_DICT)

    def visit_AugAssign(self, node):
        #TODO: maybe something smarter?
        #--> x += 1
        self.visit_Assign(node)

    def _add_target_to_variables(self, target):
        """add node from left side of assignment"""
        if hasattr(target, 'value'):
            self._add_target_to_variables(target.value)
        elif hasattr(target, 'id'):
            if not self._graph.has_node(target.id) and not target.id == "self":
                self._graph.add_node(target.id, type=TYPE_UNKNOWN)

    def visit_FunctionDef(self, node):
        #TODO: deal with function calls
        #self._graph.add_node(node.name, type=TYPE_FUNC)
        defs = node.args.defaults
        num_defs = len(defs)
        if num_defs > 0:
            for par_num, arg in enumerate(node.args.args[num_defs:]):
                for ast_type in FROM_AST_TYPE.keys():
                    if isinstance(defs[par_num], ast_type):
                        self._types[self._get_node_name(arg.id, TYPE_VARIABLE)] = FROM_AST_TYPE[ast_type]
        for arg in node.args.args:
            self._declared_inputs.append(self._get_node_name(arg.id, TYPE_VARIABLE))
        body = node.body
        func_name = node.name
        docstring = ast.get_docstring(node)
        self._parentNodes = [node] + self._parentNodes
        ast.NodeVisitor.generic_visit(self, node)
        self._parentNodes = self._parentNodes[1:]
        for arg in node.args.args:
            self._graph.add_edges_from([(self._get_node_name(arg.id, TYPE_VARIABLE), self._get_node_name(func_name, TYPE_FUNC))])


    def visit_ClassDef(self, node):
        body = node.body
        func_name = node.name
        docstring = ast.get_docstring(node)
        ast.NodeVisitor.generic_visit(self, node)

    def visit_Call(self, node):
        func_name = node.func.__dict__.get('id', None)
        if func_name is None:
            func_name = node.func.__dict__['attr']
        print "!", self._affected_var, func_name

        temp_name = func_name
        for import_pair in self.imports:
            if func_name == import_pair[0] and import_pair[1] is not None:
                temp_name = import_pair[1] + "." + func_name
                break
        self._functions[func_name] = self._get_params_from_db(temp_name)
        print temp_name,  self._get_params_from_db(temp_name)
        args = node.__dict__["args"]
        args_names = []
        for arg in args:
            try:
                args_names.append(arg.id)
            except:
                pass
        for num, par in enumerate(self._functions[func_name][0]):
            if len(args_names) == 0:
                break
            par_temp_name = self._get_node_name(args_names[0], TYPE_VARIABLE)
            if par_temp_name not in self._types.keys() and not par == "object":
                self._types[par_temp_name] = par
            args_names = args_names[1:]
        should_enter = True
        if len(self._functions[func_name][1]) > 0:
            should_enter = False
            self._curr_value += self._functions[func_name][1]
        self._look_for_vals = False
        self._affected_var = [(func_name, TYPE_FUNC)] + self._affected_var
        self._parentNodes = [node] + self._parentNodes
        ast.NodeVisitor.generic_visit(self, node)
        if should_enter and len(self._functions[func_name][1]) > 0:
            self._curr_value += self._functions[func_name][1]
        self._parentNodes = self._parentNodes[1:]
        self._affected_var = self._affected_var[1:]
        self._look_for_vals = True

        # for caller x.func()
        if len(self._affected_var) == 0:
            attr = node.func.__dict__.get('attr', None)
            if not (attr is None):
                self._graph.add_node(self._get_node_name(attr, TYPE_FUNC), type=TYPE_FUNC)
                if not node.func.__dict__['value'].id in [e[0] for e in self.imports]:
                    self._affected_var = [(node.func.__dict__['value'].id, TYPE_VARIABLE)]
                    self._save_dependency(func_name, TYPE_FUNC)
                    self._affected_var = []
            pass
        else:
            self._save_dependency(func_name, TYPE_FUNC)

    def visit_Return(self, node):
        print ast.dump(node)
        if node.value is None:
            return
        self._curr_value = []
        name = ""
        for nod in self._parentNodes:
            if isinstance(nod, ast.FunctionDef):
                name = nod.__getattribute__("name")
                #self._graph.add_edges_from([(self._get_node_name(name, TYPE_RETURN), self._get_node_name(name, TYPE_FUNC))])
                break

        #self._graph.add_node(self._get_node_name(name, TYPE_RETURN), type=TYPE_RETURN)
        if (name != ""):
            self._affected_var = [(name, TYPE_FUNC)]
        self._parentNodes = [node] + self._parentNodes
        ast.NodeVisitor.generic_visit(self, node)
        self._parentNodes = self._parentNodes[1:]
        if (name != ""):
            self._affected_var = self._affected_var[1:]
        if len(self._curr_value) >= 1:
            #self._types[self._get_node_name(name, TYPE_RETURN)] = self._curr_value[0]
            if name != "":
                self._types[self._get_node_name(name, TYPE_FUNC)] = self._curr_value[0]
                self._functions[name] = ([], self._curr_value[0])


    def visit_Print(self, node):
        self._curr_value = []
        self._graph.add_node(self._get_node_name("", TYPE_PRINT), type=TYPE_PRINT)
        self._affected_var = [("", TYPE_PRINT)]
        self._parentNodes = [node] + self._parentNodes
        #self._look_for_names_only = True
        ast.NodeVisitor.generic_visit(self, node)
        self._parentNodes = self._parentNodes[1:]
        self._affected_var = self._affected_var[1:]
        self._look_for_names_only = False

        if len(self._curr_value) >= 1:
            self._types[self._get_node_name("", TYPE_PRINT)] = self._curr_value[0]

    def visit_For(self, node):
        #TODO: ignore after getting out of the for stat
        try:
            targets = [node.target.id]
        except:
            targets = [e.id for e in node.target.elts]
        for target in targets:
            self._inner_iter.append(self._get_node_name(target, TYPE_VARIABLE))
            self._graph.add_node(self._get_node_name(target, TYPE_VARIABLE), type=TYPE_VARIABLE)
            self._affected_var = [(target, TYPE_VARIABLE)]
            self._parentNodes = [node] + self._parentNodes
            ast.NodeVisitor.generic_visit(self, node)
            self._parentNodes = self._parentNodes[1:]
            self._affected_var = self._affected_var[1:]

    def visit_Compare(self, node):
        print "COMP", ast.dump(node)
        pass

    def visit_Subscript(self, node):
        name = self._get_node_name(node.value.id, TYPE_VARIABLE)
        known_type = self._types.get(name, None)
        if known_type is None:
            self._types[name] = TYPE_ITER
        #self._look_for_names_only = True
        self._graph.add_node(name, type=TYPE_VARIABLE)
        self._affected_var = [(node.value.id, TYPE_VARIABLE)]
        self._parentNodes = [node] + self._parentNodes
        ast.NodeVisitor.generic_visit(self, node)
        self._parentNodes = self._parentNodes[1:]
        self._affected_var = self._affected_var[1:]
        self._look_for_names_only = False
        self._curr_value += [TYPE_ITER]

    def visit_Yield(self, node):
        self.visit_Return(node)

    def visit_If(self, node):
        self._graph.add_node(self._get_node_name("", TYPE_CONDITION), type=TYPE_CONDITION)
        self._affected_var = [("", TYPE_CONDITION)]
        self._parentNodes = [node] + self._parentNodes
        ast.NodeVisitor.generic_visit(self, node.__dict__["test"])
        self._parentNodes = self._parentNodes[1:]
        self._affected_var = self._affected_var[1:]
        ast.NodeVisitor.generic_visit(self, node)


    # maybe next implementation, check out if really needed
    """
    def visit_While(self, node):
        raise Exception("Unimplemented Method")

    def visit_With(self, node):
        raise Exception("Unimplemented Method")
    """

    def _get_params_from_db(self, pos_func):
        """get the function parameters, as tuple (input types, output types)"""
        splitted = pos_func.split(".")
        while len(splitted) > 0:
            try:
                if len(splitted) == 1:
                    func = DB_TYPES_PARAM.find({"net_func": ".".join(splitted)})[0]
                else:
                    func = DB_TYPES_PARAM.find({"func_name": ".".join(splitted)})[0]
                print func
                input_types = func["input"]
                if input_types is None:
                    input_types = []
                #input_types = []
                output_types = [func["output"]]
                return input_types, output_types
            except:
                pass
            splitted = splitted[1:]
        return [], []