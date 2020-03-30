from operator import sub
import subprocess
from trace import Trace
from consts import *
__author__ = 'Meital'

# get the type sigs using java ASTs (using the java code)

import networkx as nx
import matplotlib.pyplot as plt
import visit_new as v
from java_types_impl import get_java_type_set
import time


# jars
JAR_NAME = r'"C:\Users\Meital\OneDrive for Business\python_workspace\SOF_similarities\PartialCompiler.jar"'
IN_FILE = r"C:\Users\Meital\OneDrive for Business\python_workspace\SOF_similarities\tmp\java_code"
OUT_FILE = r"C:\Users\Meital\OneDrive for Business\python_workspace\SOF_similarities\tmp\java_output"


class JavaParser():
    """Java parser for getting the code flow, using AST"""
    def __init__(self):
        self._string_tree = ""
        self._graph = nx.DiGraph()

    def parse(self, code_to_parse):
        with open(IN_FILE, "wb") as writer:
            writer.write(code_to_parse)
        t = time.time()
        if call_jar(JAR_NAME, IN_FILE, OUT_FILE) == 0:
            print "jar killed"
            return 0
        print time.time() - t
        with open(OUT_FILE, "rb") as reader:
            res = reader.read()
        self._string_tree = res
        return 1

    def plot_graph(self, plot=True, file_path=""):
        """plot the flow graph (if not specified differently, False as param - and close it after 10 secs
        and return the types of the inputs and outputs, of already parsed code"""
        if self._string_tree == "":
            print "parse the tree first!"
            raise Exception("nothing to parse")
        graph = self._graph
        lines = self._string_tree.split("\n")
        types = {}
        deps = {}
        for line in lines:
            if len(line) == 0:
                continue
            #print line
            affected, deps_str = line.split("):")
            var_name, var_type = affected.split(" (")
            var_type = var_type.split(")")[0]
            types[var_name] = var_type
            deps_list = deps_str.split(", ")
            for dep in deps_list:
                if len(dep) == 0:
                    continue
                dep = dep.strip()
                dep_name, dep_type = dep.split(" (")
                dep_type = dep_type.split(")")[0]
                if dep_name not in types.keys():
                    types[dep_name] = dep_type
                deps[var_name] = deps.get(var_name, []) + [dep_name]



        for var in types:
            graph.add_node(var, type=types[var])
        for var in deps:
            for dep in deps[var]:
                graph.add_edges_from([(dep, var)])

        for key in graph.nodes():
            if graph.in_degree(key) == graph.out_degree(key) == 0 and len(graph.nodes()) > 1:
                graph.remove_node(key)
        """
        for key in graph.nodes():
            n = graph.node[key]['type']
            if graph.out_degree(key) == 0:
                if n == v.TYPE_FUNC:
                    types = self._visitor.functions.get(key[key.find("(") + 1:key.find(")")], v.TYPE_UNKNOWN)
                    ret_type = types[1][0]
                else:
                    ret_type = self._visitor.types.get(key, graph.node[key]['type'])
                if graph.node.get(v.TYPE_RETURN + "()", None) is not None and not key == v.TYPE_RETURN + "()" and not n == v.TYPE_CONDITION:
                    graph.add_node(v.TYPE_RETURN + "()", type=ret_type)
                    graph.add_edges_from([(key, v.TYPE_RETURN + "()")])
        """

        pos = nx.spring_layout(graph)
        nx.draw_networkx(graph, pos, node_color='w', node_shape='s')

        for key in pos.keys():
            x, y = pos[key]
            plt.text(x, y - 0.07, s=graph.node[key]['type'], bbox=dict(facecolor='pink', alpha=0.5), horizontalalignment='center')

        input_vertexes = [graph.node[e[0]]['type'] for e in graph.in_degree(pos.keys()).items() if e[1] == 0
                          and not graph.node[e[0]]['type'] == "void" and not e[0][e[0].find("(") + 1:e[0].find(")")] in ['""', "[]"]
                          and not graph.node[e[0]]['type'] in [v.TYPE_CONDITION, v.TYPE_VARIABLE, v.TYPE_FUNC]]
        output_vertexes = [graph.node[e[0]]['type'] for e in graph.out_degree(pos.keys()).items() if e[1] == 0
                           and not graph.node[e[0]]['type'] in [v.TYPE_CONDITION, v.TYPE_VARIABLE]]
        """
        if len(output_vertexes) == 0 and self._visitor.last_changed is not None:
            last_type = self._visitor.types.get(self._visitor.last_changed, None)
            if last_type is not None:
                output_vertexes = [last_type]

        if len(self._visitor.inputs) > 0:
            input_vertexes = []
            for par in self._visitor.inputs:
                x = self._visitor.types.get(par, None)
                if x is not None:
                    input_vertexes += [x]
        """
        final_in = []
        final_out = []
        for e in input_vertexes:
            final_in += get_java_type_set(e)
        for e in output_vertexes:
            final_out += get_java_type_set(e)

        if plot:
            plt.show(block=True)
            plt.close()
        if not file_path == "":
            plt.savefig(file_path)
        plt.clf()
        return final_in, final_out


def save_graph(code_snip, file_path=""):
    """save the code_snip graph to file_path,
    returns input and output types"""
    try:
        parser = JavaParser()
        if parser.parse(code_snip) == "0":
            return None, None
        in_v, out_v = parser.plot_graph(False, file_path)
    except Exception as e:
        print "parsing problem", e
        in_v = out_v = None
    #print in_v, out_v
    return in_v, out_v

import subprocess, shlex
from threading import Timer


def run(cmd, timeout_sec):
    """run the jar with timeout"""
    DB_KILLED = client.flag['killed']
    DB_KILLED.insert({"killed": False})
    proc = subprocess.Popen(cmd, shell=True)
    def kill_proc(p):
        p.kill()
        print "killed"
        DB_KILLED.insert({"killed": True})
    timer = Timer(timeout_sec, kill_proc, [proc])
    timer.start()
    stdout, stderr = proc.communicate()
    timer.cancel()
    flag = True if DB_KILLED.find({}).count() > 1 else False
    DB_KILLED.drop()
    if flag:
        return "0"
    else:
        return "1"


def call_jar(jar_name, in_file, out_file):
    """call the external jar to get the sigs"""
    #cmd = r'"C:\Program Files\Java\jre1.8.0_25\bin\javaw.exe" -Dfile.encoding=UTF-8 -classpath "C:\Users\Meital\OneDrive for Business\com.meital\target\classes;C:\Users\Meital\OneDrive for Business\com.meital\lib\org.eclipse.jdt.core_3.8.3.v20130121-145325.jar;C:\Users\Meital\.m2\repository\com\sun\jersey\jersey-server\1.8\jersey-server-1.8.jar;C:\Users\Meital\.m2\repository\asm\asm\3.1\asm-3.1.jar;C:\Users\Meital\.m2\repository\com\sun\jersey\jersey-core\1.8\jersey-core-1.8.jar;C:\Users\Meital\.m2\repository\com\sun\jersey\jersey-json\1.8\jersey-json-1.8.jar;C:\Users\Meital\.m2\repository\org\codehaus\jettison\jettison\1.1\jettison-1.1.jar;C:\Users\Meital\.m2\repository\stax\stax-api\1.0.1\stax-api-1.0.1.jar;C:\Users\Meital\.m2\repository\com\sun\xml\bind\jaxb-impl\2.2.3-1\jaxb-impl-2.2.3-1.jar;C:\Users\Meital\.m2\repository\javax\xml\bind\jaxb-api\2.2.2\jaxb-api-2.2.2.jar;C:\Users\Meital\.m2\repository\javax\xml\stream\stax-api\1.0-2\stax-api-1.0-2.jar;C:\Users\Meital\.m2\repository\javax\activation\activation\1.1\activation-1.1.jar;C:\Users\Meital\.m2\repository\org\codehaus\jackson\jackson-core-asl\1.7.1\jackson-core-asl-1.7.1.jar;C:\Users\Meital\.m2\repository\org\codehaus\jackson\jackson-mapper-asl\1.7.1\jackson-mapper-asl-1.7.1.jar;C:\Users\Meital\.m2\repository\org\codehaus\jackson\jackson-jaxrs\1.7.1\jackson-jaxrs-1.7.1.jar;C:\Users\Meital\.m2\repository\org\codehaus\jackson\jackson-xc\1.7.1\jackson-xc-1.7.1.jar;C:\Users\Meital\.m2\repository\com\google\code\maven-play-plugin\org\eclipse\jdt\org.eclipse.jdt.core\3.8.0.v_C18\org.eclipse.jdt.core-3.8.0.v_C18.jar;C:\Users\Meital\.m2\repository\org\eclipse\core\org.eclipse.core.contenttype\3.4.100.v20100505-1235\org.eclipse.core.contenttype-3.4.100.v20100505-1235.jar;C:\Users\Meital\.m2\repository\org\eclipse\equinox\org.eclipse.equinox.registry\3.5.0.v20100503\org.eclipse.equinox.registry-3.5.0.v20100503.jar;C:\Users\Meital\.m2\repository\org\eclipse\core\org.eclipse.core.jobs\3.5.0.v20100515\org.eclipse.core.jobs-3.5.0.v20100515.jar;C:\Users\Meital\.m2\repository\org\eclipse\core\org.eclipse.core.resources\3.6.0.v20100526-0737\org.eclipse.core.resources-3.6.0.v20100526-0737.jar;C:\Users\Meital\.m2\repository\org\eclipse\core\org.eclipse.core.expressions\3.4.200.v20100505\org.eclipse.core.expressions-3.4.200.v20100505.jar;C:\Users\Meital\.m2\repository\org\eclipse\core\org.eclipse.core.filesystem\1.3.0.v20100526-0737\org.eclipse.core.filesystem-1.3.0.v20100526-0737.jar;C:\Users\Meital\.m2\repository\org\eclipse\core\org.eclipse.core.runtime\3.6.0.v20100505\org.eclipse.core.runtime-3.6.0.v20100505.jar;C:\Users\Meital\.m2\repository\org\eclipse\equinox\org.eclipse.equinox.app\1.3.0.v20100512\org.eclipse.equinox.app-1.3.0.v20100512.jar;C:\Users\Meital\.m2\repository\org\eclipse\osgi\org.eclipse.osgi.services\3.2.100.v20100503\org.eclipse.osgi.services-3.2.100.v20100503.jar;C:\Users\Meital\.m2\repository\javax\servlet\servlet-api\2.5\servlet-api-2.5.jar;C:\Users\Meital\.m2\repository\org\apache\felix\org.osgi.foundation\1.2.0\org.osgi.foundation-1.2.0.jar;C:\Users\Meital\.m2\repository\org\eclipse\equinox\org.eclipse.equinox.common\3.6.0.v20100503\org.eclipse.equinox.common-3.6.0.v20100503.jar;C:\Users\Meital\.m2\repository\org\eclipse\osgi\org.eclipse.osgi\3.6.0.v20100517\org.eclipse.osgi-3.6.0.v20100517.jar;C:\Users\Meital\.m2\repository\org\eclipse\equinox\org.eclipse.equinox.preferences\3.3.0.v20100503\org.eclipse.equinox.preferences-3.3.0.v20100503.jar;C:\Users\Meital\.m2\repository\org\eclipse\org.eclipse.osgi\3.8.0.v20120529-1548\org.eclipse.osgi-3.8.0.v20120529-1548.jar;C:\Users\Meital\.m2\repository\org\mongodb\mongo-java-driver\2.11.1\mongo-java-driver-2.11.1.jar;C:\Users\Meital\.m2\repository\com\google\code\gson\gson\2.2.4\gson-2.2.4.jar" com.codota.livecode.compiler.MainComplier'
    cmd = r'"C:\Program Files\Java\jdk1.8.0_25\bin\javaw.exe" -Dfile.encoding=UTF-8 -classpath "C:\Users\Meital\OneDrive for Business\com.meital\target\classes;C:\Users\Meital\OneDrive for Business\com.meital\lib\org.eclipse.jdt.core_3.8.3.v20130121-145325.jar;C:\Users\Meital\OneDrive for Business\com.meital\commons-io-2.4.jar;C:\Users\Meital\.m2\repository\com\sun\jersey\jersey-server\1.8\jersey-server-1.8.jar;C:\Users\Meital\.m2\repository\asm\asm\3.1\asm-3.1.jar;C:\Users\Meital\.m2\repository\com\sun\jersey\jersey-core\1.8\jersey-core-1.8.jar;C:\Users\Meital\.m2\repository\com\sun\jersey\jersey-json\1.8\jersey-json-1.8.jar;C:\Users\Meital\.m2\repository\org\codehaus\jettison\jettison\1.1\jettison-1.1.jar;C:\Users\Meital\.m2\repository\stax\stax-api\1.0.1\stax-api-1.0.1.jar;C:\Users\Meital\.m2\repository\com\sun\xml\bind\jaxb-impl\2.2.3-1\jaxb-impl-2.2.3-1.jar;C:\Users\Meital\.m2\repository\javax\xml\bind\jaxb-api\2.2.2\jaxb-api-2.2.2.jar;C:\Users\Meital\.m2\repository\javax\xml\stream\stax-api\1.0-2\stax-api-1.0-2.jar;C:\Users\Meital\.m2\repository\javax\activation\activation\1.1\activation-1.1.jar;C:\Users\Meital\.m2\repository\org\codehaus\jackson\jackson-core-asl\1.7.1\jackson-core-asl-1.7.1.jar;C:\Users\Meital\.m2\repository\org\codehaus\jackson\jackson-mapper-asl\1.7.1\jackson-mapper-asl-1.7.1.jar;C:\Users\Meital\.m2\repository\org\codehaus\jackson\jackson-jaxrs\1.7.1\jackson-jaxrs-1.7.1.jar;C:\Users\Meital\.m2\repository\org\codehaus\jackson\jackson-xc\1.7.1\jackson-xc-1.7.1.jar;C:\Users\Meital\.m2\repository\com\google\code\maven-play-plugin\org\eclipse\jdt\org.eclipse.jdt.core\3.8.0.v_C18\org.eclipse.jdt.core-3.8.0.v_C18.jar;C:\Users\Meital\.m2\repository\org\eclipse\core\org.eclipse.core.contenttype\3.4.100.v20100505-1235\org.eclipse.core.contenttype-3.4.100.v20100505-1235.jar;C:\Users\Meital\.m2\repository\org\eclipse\equinox\org.eclipse.equinox.registry\3.5.0.v20100503\org.eclipse.equinox.registry-3.5.0.v20100503.jar;C:\Users\Meital\.m2\repository\org\eclipse\core\org.eclipse.core.jobs\3.5.0.v20100515\org.eclipse.core.jobs-3.5.0.v20100515.jar;C:\Users\Meital\.m2\repository\org\eclipse\core\org.eclipse.core.resources\3.6.0.v20100526-0737\org.eclipse.core.resources-3.6.0.v20100526-0737.jar;C:\Users\Meital\.m2\repository\org\eclipse\core\org.eclipse.core.expressions\3.4.200.v20100505\org.eclipse.core.expressions-3.4.200.v20100505.jar;C:\Users\Meital\.m2\repository\org\eclipse\core\org.eclipse.core.filesystem\1.3.0.v20100526-0737\org.eclipse.core.filesystem-1.3.0.v20100526-0737.jar;C:\Users\Meital\.m2\repository\org\eclipse\core\org.eclipse.core.runtime\3.6.0.v20100505\org.eclipse.core.runtime-3.6.0.v20100505.jar;C:\Users\Meital\.m2\repository\org\eclipse\equinox\org.eclipse.equinox.app\1.3.0.v20100512\org.eclipse.equinox.app-1.3.0.v20100512.jar;C:\Users\Meital\.m2\repository\org\eclipse\osgi\org.eclipse.osgi.services\3.2.100.v20100503\org.eclipse.osgi.services-3.2.100.v20100503.jar;C:\Users\Meital\.m2\repository\javax\servlet\servlet-api\2.5\servlet-api-2.5.jar;C:\Users\Meital\.m2\repository\org\apache\felix\org.osgi.foundation\1.2.0\org.osgi.foundation-1.2.0.jar;C:\Users\Meital\.m2\repository\org\eclipse\equinox\org.eclipse.equinox.common\3.6.0.v20100503\org.eclipse.equinox.common-3.6.0.v20100503.jar;C:\Users\Meital\.m2\repository\org\eclipse\osgi\org.eclipse.osgi\3.6.0.v20100517\org.eclipse.osgi-3.6.0.v20100517.jar;C:\Users\Meital\.m2\repository\org\eclipse\equinox\org.eclipse.equinox.preferences\3.3.0.v20100503\org.eclipse.equinox.preferences-3.3.0.v20100503.jar;C:\Users\Meital\.m2\repository\org\eclipse\org.eclipse.osgi\3.8.0.v20120529-1548\org.eclipse.osgi-3.8.0.v20120529-1548.jar;C:\Users\Meital\.m2\repository\org\mongodb\mongo-java-driver\2.11.1\mongo-java-driver-2.11.1.jar;C:\Users\Meital\.m2\repository\com\google\code\gson\gson\2.2.4\gson-2.2.4.jar" com.codota.livecode.compiler.MainComplier'
    cmd += ' "' + in_file + '" ' + '"' + out_file + '"'
    return run(cmd, 10)


if __name__ == "__main__":
    code = """minimum + rn.nextInt(maxValue - minvalue + 1)"""
    save_graph(code, "temp/aaa")
    exit()
    j = JavaParser()
    j.parse(code)
    j.plot_graph()
