__author__ = 'Meital'
# build the func to input-output db (python)
from pyparsing import *
from consts import *
from cStringIO import StringIO
import sys
import re

PY_DB = client.python
DB_TYPES_PARAM = PY_DB.func_to_types_new
FIRST = False


def lib2params(module, name='', append=False):
    """get the parameters of the function within specific library"""""
    f2r = map(lambda x: (x, getattr(module, x).__doc__), dir(module))
    f2r = filter(lambda x: not(x[1] is None) and "->" in x[1], f2r)
    f2r = filter(lambda x: x[1].startswith(x[0]), f2r)
    f2r = map(lambda x: (x[0], x[1].split('\n')[0]), f2r)
    f2r = map(lambda x: (x[0], ((x[1])[len(x[0]):].strip())), f2r)

    def func2types(doc):
        """function to its return value"""
        splitted = doc.split("->")
        retval =  splitted[1].strip()

        arguments = splitted[0].strip().replace("(", "").replace(")", "").replace("[", "").replace("]", "")
        if len(arguments) == 0:
            arguments = None
        else:
            arguments = map(lambda x: x.split("=")[0].strip().split("-")[0].strip(), arguments.split(","))
        return arguments, retval

    f2r = map(lambda x: (x[0], func2types(x[1])), f2r)
    if append:
        f2r = map(lambda x: (str(name) + "." + x[0], x[1]), f2r)
    return f2r


def save_funcs_db():
    """import to db the python function and its ret val"""
    DB_TYPES_PARAM.drop()
    DB_TYPES_PARAM.ensure_index("func_name", unique=True)

    #for built-ins
    all_funcs = lib2params(__builtins__)

    #for all other modules
    old_stdout = sys.stdout
    sys.stdout = mystdout = StringIO()
    help('modules')
    sys.stdout = old_stdout

    modules = ("\n".join(mystdout.getvalue().split('\n')[4:-5]))
    modules = filter(lambda x: len(x) > 0, re.split("\s", modules))
    pprint(modules)
    for module in modules:
        my_module = None
        try:
            my_module = __import__(module)
            all_funcs += lib2params(my_module, module, True)
        except:
            pass
        if not my_module is None:
            for sub_module in dir(my_module):
                try:
                    if str(type(getattr(my_module, sub_module))) == "<type 'module'>":
                        my_sub_module = __import__(module + "." + sub_module)
                        all_funcs += lib2params(my_sub_module, module + "." + sub_module, True)
                except:
                    pass

    pprint(all_funcs)
    for func in all_funcs:
        try:
            DB_TYPES_PARAM.insert({"func_name": func[0], "input": func[1][0], "output": func[1][1], "net_func": func[0].split(".")[-1]})
            #print func
            pass
        except:
            pass


def get_python_type_set(type_name):
    """return the set type of the given type"""
    if "None" in type_name:
        return ""
    type_name = type_name.lower()
    if type_name in SET_OF_CLASSES:
        return type_name
    if "iterable" in type_name:
        return "iterable"
    if "list" in type_name or "tuple" in type_name or "iterator" in type_name:
        return "list"
    if "set" in type_name:
        return "set"
    if "byte" in type_name or "character" in type_name or "string" in type_name or "unicode" in type_name:
        return "string"
    if "integer" in type_name or "number" in type_name or "long" in type_name or "int" in type_name:
        return "number"
    if "dictionary" in type_name or "dict" in type_name:
        return "dictionary"
    if "file" in type_name:
        return "file"
    if "bool" in type_name:
        return "bool"
    return "object"


def get_types(code):
    """get python types, very naive approach"""
    code_lines = [e.replace(">>>", "").strip() for e in code.split("\n")]
    types_list = []

    #macros
    chars = Word(alphanums + "_" + "-" + " ")
    fun_chars = Word(alphanums + "_" + "-" + ".")
    dic_chars = Word(alphanums + "_" + "-" + ":" + "," + " " + "'" + '"' + "(" + ")" + ".")
    numbers_chars = Word(nums + "-" + "." + " ")
    in_def_chars = Word(alphanums + "_" + "-" + " " + "=" + "'" + '"' + ",")
    string_chars = Word("".join(c for c in string.printable if not c == "'" and not c == '"'))
    import_macro = Literal("import") + chars
    number_assignment = Literal("=") + numbers_chars
    string_assignment = Literal("=") + Literal('"') + string_chars + Literal('"') | Literal("=") + Literal("'") + string_chars + Literal("'")
    string_macro = string_assignment | Literal('"') + string_chars + Literal('"') | Literal("'") + string_chars + Literal("'")
    string_with_print_macro = Optional("print") + string_macro
    function_def_macro = Literal("def") + chars + Literal("(") + in_def_chars + Literal("):")
    dictionary_macro = Literal("{") + Optional(dic_chars) + Literal("}")
    list_macro = Literal("[") + Optional(dic_chars) + Literal("]") | Keyword("for")
    function_name_macro = fun_chars.setResultsName("name") + Literal("(")
    bool_assignment = Literal("=") + Keyword("True") | Literal("=") + Keyword("False")
    bool_macro = Keyword("if") | Keyword("while")
    #TODO: (optional) ignore comments

    check_macro = lambda macro, line: len(macro.searchString(line)) > 0

    for line in code_lines:
        line_types = []
        if check_macro(import_macro, line):
            continue
        if check_macro(function_def_macro, line):
            continue
        if check_macro(number_assignment, line):
            line_types += ["number"]
        if check_macro(dictionary_macro, line):
            line_types += ["dictionary"]
        if check_macro(list_macro, line):
            line_types += ["list"]
        if check_macro(string_with_print_macro, line):
            if not 'print' == string_with_print_macro.searchString(line)[0][0]:
                line_types += ["string"]
        if check_macro(bool_macro, line):
            line_types += ["bool"]
        if check_macro(function_name_macro, line):
            #only the outer func is currently relevant
            for t, s, e in function_name_macro.scanString(line):
                pos_func = t.name
                break
            pos_func = pos_func.split(" ")[-1]
            in_t, out_t = get_params_from_db(pos_func)
            line_types += in_t
            line_types += out_t
        #prevent default boolean values from being recognized as bool
        elif check_macro(bool_assignment, line):
            line_types += ["bool"]
        types_list += [list(set(line_types))]
        print types_list, line
    ret_val = []
    for line_list in types_list:
        line_set = set()
        for t in line_list:
            x = get_python_type_set(t)
            if not x is "":
                line_set.add(x)
        ret_val += list(line_set)
    return ret_val


def get_params_from_db(pos_func):
    """get the function parameters, as tuple (input types, output types)"""
    splitted = pos_func.split(".")
    while len(splitted) > 0:
        try:
            if len(splitted) == 1:
                func = DB_TYPES_PARAM.find({"net_func": ".".join(splitted)})[0]
            else:
                func = DB_TYPES_PARAM.find({"func_name": ".".join(splitted)})[0]
            #input_types = func["input"]
            input_types = []
            output_types = [func["output"]]
            return input_types, output_types
        except:
            pass
        splitted = splitted[1:]
    return [], []


if __name__ == "__main__":
    save_funcs_db()
    '''
    if FIRST:
        save_funcs_db()
    CODE = """for i in xrange(len(somelist) - 1, -1, -1):
    if some_condition(somelist, i):
        del somelist[i]"""
    print get_types(CODE)
    '''