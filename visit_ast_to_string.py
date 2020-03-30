__author__ = 'Meital'
# visitor that is used for the string creation when using python specific syntactic similarity
import ast


class AnalysisNodeVisitor(ast.NodeVisitor):
    """the ast visiotr class"""
    def __init__(self):
        self._string = []

    @property
    def string(self):
        return self._string


    def generic_visit(self, node):
        if type(node) not in [ast.Import, ast.Module, ast.alias, ast.ImportFrom]:
            self._string.append(type(node).__name__)
        ast.NodeVisitor.generic_visit(self, node)

    def visit_Call(self, node):
        # save more that about function calls
        try:
            print ast.dump(node)
            self._string.append(type(node).__name__ + " - " + " ".join([node.func.attr] * 3))
        except:
            self._string.append(type(node).__name__ + " - internal")
        ast.NodeVisitor.generic_visit(self, node)


