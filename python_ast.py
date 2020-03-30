__author__ = 'Meital'
# python specific type signatures
import ast
import networkx as nx
import matplotlib.pyplot as plt
from tokenize import generate_tokens, untokenize, INDENT
from cStringIO import StringIO
import visit_new as v
from python_types_impl import get_python_type_set


class PythonParser():
    """Python parser for getting the code flow, using AST"""
    def __init__(self):
        self.string_tree = ""
        self._visitor = None
        self._ast = None

    # _dedent borrowed from the myhdl package (www.myhdl.org)
    def _dedent(self, s):
        """Dedent python code string. not working that well"""
        result = [t[:2] for t in generate_tokens(StringIO(s).readline)]
        # set initial indent to 0 if any
        if result[0][0] == INDENT:
            result[0] = (INDENT, '')
        return untokenize(result)

    def parse(self, code_to_parse):
        """parse the given code"""
        code_to_parse = self._dedent(code_to_parse)
        while True:
            try:
                parsed_ast = ast.parse(code_to_parse)
                break
            except Exception as e:
                if "invalid syntax (<unknown>, line" in str(e):
                    cl = code_to_parse.split("\n")
                    prob_line = int(str(e).split("invalid syntax (<unknown>, line ")[1].split(")")[0])
                    if cl[prob_line - 1].startswith(">>>"):
                        code_to_parse = "\n".join(cl[:prob_line-1] +[cl[prob_line-1].replace(">>>", "").strip()] + cl[prob_line:])
                    else:
                        code_to_parse = "\n".join(cl[:prob_line - 1] + cl[prob_line:])
                else:
                    print e
                    break
        self._visitor = v.AnalysisNodeVisitor()
        self._ast = parsed_ast
        self.string_tree = ast.dump(parsed_ast)
        self._visitor.visit(parsed_ast)
        print "FUNCS:", self._visitor.functions
        print "IMPORTS:", self._visitor.imports
        print "TYPES:", self._visitor.types
        print "KNOWN INPUTS", self._visitor.inputs
        print "NOT_IN", self._visitor.inner_iter
        return self._visitor

    def plot_graph(self, plot=True, file_path=""):
        """plot the flow graph (if not specified differently, False as param - and close it after 10 secs
        and return the types of the inputs and outputs, of already parsed code"""
        if self._visitor is None or self._visitor.graph is None:
            if len(self.flow_with_types) == 0:
                print "parse the tree first!"
                return None, None
        graph = self._visitor.graph

        for known_var in self._visitor.types.keys():
            graph.add_node(known_var, type=self._visitor.types[known_var])

        for key in graph.nodes():
            n = graph.node[key]['type']

            #remove conditions deps
            if n == v.TYPE_CONDITION:
                graph.remove_node(key)

        for key in graph.nodes():
            if graph.in_degree(key) == graph.out_degree(key) == 0 and len(graph.nodes()) > 1:
                graph.remove_node(key)
            if graph.in_degree(key) == 0 and key[key.find("(") + 1:key.find(")")] in [e[0] for e in self._visitor.imports]:
                graph.remove_node(key)
        for key in graph.nodes():
            n = graph.node[key]['type']
            if graph.out_degree(key) == 0:
                if n == v.TYPE_FUNC:
                    types = self._visitor.functions.get(key[key.find("(") + 1:key.find(")")], v.TYPE_UNKNOWN)
                    if not types == v.TYPE_UNKNOWN:
                        try:
                            ret_type = types[1][0]
                        except:
                            ret_type = v.TYPE_UNKNOWN
                    else:
                        ret_type = types
                else:
                    ret_type = self._visitor.types.get(key, graph.node[key]['type'])
                # was in the if too: graph.node.get(v.TYPE_RETURN + "()", None) is not None and
                if not v.TYPE_RETURN in key and n not in [v.TYPE_CONDITION, v.TYPE_UNKNOWN, v.TYPE_VARIABLE] and v.TYPE_PRINT + "()" not in graph.nodes():
                    graph.add_node(v.TYPE_RETURN + "()", type=ret_type)
                    graph.add_edges_from([(key, v.TYPE_RETURN + "()")])


        pos = nx.spring_layout(graph)
        nx.draw_networkx(graph, pos, node_color='w', node_shape='s')

        for key in pos.keys():
            x, y = pos[key]
            plt.text(x, y - 0.07, s=graph.node[key]['type'], bbox=dict(facecolor='pink', alpha=0.5), horizontalalignment='center')

        input_vertexes = [graph.node[e[0]]['type'] for e in graph.in_degree(pos.keys()).items() if e[1] == 0
                          and not graph.node[e[0]]['type'] == "void" and not e[0][e[0].find("(") + 1:e[0].find(")")] in ['""', "[]"]
                          and not graph.node[e[0]]['type'] in [v.TYPE_CONDITION, v.TYPE_VARIABLE, v.TYPE_RETURN] and e[0] not in self._visitor.inner_iter]
        output_vertexes = [graph.node[e[0]]['type'] for e in graph.out_degree(pos.keys()).items() if e[1] == 0
                           and not graph.node[e[0]]['type'] in [v.TYPE_CONDITION, v.TYPE_VARIABLE, v.TYPE_FUNC]]

        if len(output_vertexes) == 0 and self._visitor.last_changed is not None:
            last_type = self._visitor.types.get(self._visitor.last_changed, None)
            if last_type is not None:
                output_vertexes = [last_type]

        if len(self._visitor.inputs) > 0 and len(self._ast.body) == 1 and isinstance(self._ast.body[0], ast.FunctionDef):
            input_vertexes = []
            for par in self._visitor.inputs:
                x = self._visitor.types.get(par, None)
                if x is not None:
                    input_vertexes += [x]
        final_in = [get_python_type_set(e) for e in input_vertexes]
        final_out = [get_python_type_set(e) for e in output_vertexes]
        print input_vertexes, output_vertexes
        print final_in, final_out
        if plot:
            plt.show(block=True)
            plt.close()
        if not file_path == "":
            plt.savefig(file_path)
        plt.clf()
        return final_in, final_out
        #return input_vertexes, output_vertexes


def save_graph(code_snip, file_path=""):
    """save the code_snip graph to file_path,
    returns input and output types"""
    try:
        parser = PythonParser()
        parser.parse(code_snip)
        in_v, out_v = parser.plot_graph(False, file_path)
    except Exception as e:
        print "parsing problem", e
        in_v = out_v = None
    print in_v, out_v
    return in_v, out_v


def print_graph(code):
    """prints the graph of the given code"""
    parser = PythonParser()
    parser.parse(code)
    return parser.plot_graph(True)


if __name__ == "__main__":
    # import code examples
    import ast_code_examples
    print_graph(ast_code_examples.code)