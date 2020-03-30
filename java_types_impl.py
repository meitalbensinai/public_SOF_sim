__author__ = 'Meital'
# mostly not in use, the types are extracted differently using external har and the file java_ast.py
from bs4 import BeautifulSoup
import urllib2
import re
from pyparsing import *
from consts import *


all_classes = ["byte", "short", "int", "long", "float", "double", "char", "String", "boolean"]
ignored_classes = ["system"]


def build_class_Hierarchy():
    """get java known classes"""
    global all_classes
    url = "http://docs.oracle.com/javase/7/docs/api/allclasses-noframe.html"
    usock = urllib2.urlopen(url)
    data = usock.read()
    usock.close()
    soup = BeautifulSoup(data, 'html.parser')
    for link in soup.find_all('a'):
        if " in " in link.get("title"):
            all_classes.append(link.text)
    return all_classes


def extract_types(snippet, all_classes):
    """for given code snippet - extract types:
    primitives, known classes, generics and arrays"""
    annotation = Literal("@")
    known_classes = MatchFirst(map(Keyword, all_classes))
    space = oneOf([" "])
    types_ = Combine(Optional(annotation) + known_classes)
    string_chars = Word("".join(c for c in string.printable if not c == "'" and not c == '"'))
    #TODO: to add generic in generic use the Foreword() func, to allowed recursion
    classes_ = (types_ | Word(alphas, min=1))
    generic_types_ = Combine(types_+"<"+classes_+","+ZeroOrMore(space)+classes_+">") | \
                     Combine(types_+"<"+classes_+">") | Combine(types_ + "[" + ZeroOrMore(Word(nums)) + "]") | types_
    bool_macro = Keyword("if") | Keyword("while")
    string_macro = Literal('"') + string_chars + Literal('"') | Literal("'") + string_chars + Literal("'")
    string_keyword = Literal("String")
    base_types = []
    results = generic_types_.scanString(snippet)

    new_line_places = [i for i, ltr in enumerate(snippet) if ltr == "\n"][::2]
    lines = []
    for i in results:
        res = i[0][0]
        if i[0][0].endswith(" "):
            res = res[:-1]
        base_types.append(res.replace(" ", ""))
        lines.append(get_line(i, new_line_places))
    ret_val = []
    prev_found = []
    for num, t in enumerate(base_types):
        if len(annotation.searchString(t)) == 0:
            x = get_java_type_set(t)
            if x == prev_found and not num == 0 and lines[num - 1] == lines[num]:
                continue
            ret_val += x
            prev_found = x
    bool_vals = len(bool_macro.searchString(snippet))
    strings = string_macro.scanString(snippet)
    already_counted_strings = string_keyword.scanString(snippet)
    string_vals = 0
    for s in strings:
        found = False
        for a_s in already_counted_strings:
            if get_line(s, new_line_places) == get_line(a_s, new_line_places):
                found = True
                break
        if not found:
            string_vals += 1
    ret_val += ["bool"] * bool_vals + ["string"] * string_vals
    return ret_val


def get_line(found, new_lines):
    """get the line of found type,
    used to prevent multi entries for the same variable"""
    print found
    for line, index in enumerate(new_lines):
        if found[1] < index:
            return line
    return line + 1


def get_java_type_set(type_name):
    """return the set type of the given type"""
    pos_types = []
    generic_out_re = re.compile(r'<.*?>', re.DOTALL)
    array_out_re = re.compile(r'[.*?]', re.DOTALL)
    in_generic = re.search('%s(.*?)%s' % ("<", ">"), type_name)
    if not in_generic is None:
        pos_types += [e.strip().lower() for e in in_generic.group(1).split(",")]
    pos_types.append(generic_out_re.sub("", type_name).lower())
    ret_types = []
    for type_name in pos_types:
        if type_name in ignored_classes:
            return []
        if "[" in type_name:
            ret_types.append("list")
            type_name = array_out_re.sub("", type_name).lower()
        if type_name in ['byte', 'char', 'string', "unicode"] or "sting" in type_name:
            ret_types.append("string")
        elif type_name in ['short', 'int', 'long', 'float', 'double', 'number']:
            ret_types.append("number")
        elif type_name in ["boolean"]:
            ret_types.append("bool")
        elif "map" in type_name:
            ret_types.append("dictionary")
        elif "list" in type_name:
            ret_types.append("list")
        elif "set" in type_name:
            ret_types.append("set")
        elif "file" in type_name:
            ret_types.append("file")
        elif "stream" in type_name:
            ret_types.append("stream")
        elif len(ret_types) == 0:
            ret_types.append("object")
    return ret_types

if __name__ == "__main__":
    pass
