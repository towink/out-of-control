import networkx as nx
import matplotlib.pyplot as plt
import functools

filename = "nand"
with open(filename + ".pm", 'r') as file:
    code_with_comments = file.read()

# Strip code of comments (a lot of them contain the word "module", which confuses the module unroller)
code = ""
start_line = -1
while True:
    end_line = code_with_comments.find("\n", start_line + 1)
    if end_line == -1:
        break
    line = code_with_comments[start_line+1:end_line]
    comment = line.find("//")
    if comment != -1:
        line = line[0:comment]

    code += line + "\n"

    start_line = end_line

# Unroll the modules:

modules = dict() # Stores all modules that aren't just a copy of an existing one
start = 0

while True:

    start_module = code.find("module", start)
    if start_module == -1:
        break
    start += 1

    start_name = start_module + len("module ")
    end_name = start_name
    while code[end_name].isalnum():
        end_name += 1
    name = code[start_name:end_name]

    end_module = code.find("endmodule", start_module)

    # Figure out whether this is a copy of an existing module or a new one

    pos = end_name
    while True:
        cur = code[pos]
        if cur == "\n": # Assume that we found a new module (this is just an approximation):
            content = code[end_name:end_module - 1]
            modules[name] = content
            print("Found new module: " + name)
            break
        if cur == "=": # This module is a copy of an existing one
            pos += 1
            while code[pos] == " ":
                pos += 1

            copied_name = ""
            while code[pos].isalnum():
                copied_name += code[pos]
                pos += 1

            print("Found copy module: " + name + " (copy of " + copied_name + ")")


            while code[pos] != "[":
                pos += 1
            pos += 1


            # Try to do the variable replacement. This will behave incorrectly if there are variables
            # x and y, x is replaced, y is not replaced and the name of x is a prefix of the name of y.
            # If both x and y are replaced, the should not be an issue

            replacements = []
            lhs = ""
            rhs = None
            while True:
                cur = code[pos]
                pos += 1

                if cur == "]":
                    break
                if cur.isalnum():
                    if rhs is None:
                        lhs += cur
                    else:
                        rhs += cur
                else:
                    if lhs != "" and rhs is None:
                        rhs = ""
                    if rhs is not None and rhs != "":
                        replacements.append((lhs, rhs))
                        lhs = ""
                        rhs = None

            # Sort the replacements by descending length to avoid the above-described issues
            # with the prefixes:

            def key_compare(item1, item2):
                l1 = len(item1[0])
                l2 = len(item2[0])
                if l1 < l2:
                    return 1
                if l1 == l2:
                    return 0
                return -1

            replacements = sorted(replacements, key=functools.cmp_to_key(key_compare))
            print(replacements)

            content = modules[copied_name]
            for i, rep in enumerate(replacements):
                # First use temporary name so the replaced variables aren't replaced again. Also ensure the
                # name has constant length to avoid the issues with prefixes as described above
                content = content.replace(rep[0], "temp" + f'{i:03}')
            for i, rep in enumerate(replacements):
                content = content.replace("temp" + f'{i:03}', rep[1])

            code = code[0:end_name] + " " + content + code[end_module:]
            end_module = code.find("endmodule", start_module)

            break
        pos += 1

    start = end_module + len("endmodule")

dependencies = dict()

# List of keywords according to the prism language specification (https://www.prismmodelchecker.org/manual/ThePRISMLanguage/ModulesAndVariables):
keywords = {"A","bool","clock","const","ctmc","C","double","dtmc","E","endinit","endinvariant","endmodule","endrewards","endsystem","false","formula","filter","func","F","global","G","init","invariant","I","int","label","max","mdp","min","module","X","nondeterministic","Pmax","Pmin","P","probabilistic","prob","pta","rate","rewards","Rmax","Rmin","R","S","stochastic","system","true","U","W"}

# Search for all occurrences of '=
start = 0
while True:
    location = code.find("\'=", start)
    if location == -1:
        break
    start = location + 1

    lside_end = location - 1
    while code[lside_end] == ' ':
        lside_end -= 1

    lside_start = lside_end
    while code[lside_start].isalnum() or code[lside_start] == "_":
        lside_start -= 1

    lside = code[lside_start + 1: lside_end + 1]

    rside_vars = set() # Set of all vars that occur on the rhs
    rside_start = location + 2
    open_paren_count = 0
    inside_var = False
    current_var = ""
    while True:
        character = code[rside_start]
        rside_start += 1

        if inside_var:
            if character.isalnum() or character == "_":
                current_var += character
            else:
                inside_var = False
                if current_var not in keywords:
                    rside_vars.add(current_var)
                current_var = ""
        else:
            if character.isalpha() or character == "_":
                inside_var = True
                current_var = character

        if character == "(":
            open_paren_count += 1
        if character == ")":
            open_paren_count -= 1
        if open_paren_count < 0:
            break

    if lside not in dependencies:
        dependencies[lside] = set()
    dependencies[lside].update(rside_vars)

    rside_string = ""
    for rside_var in rside_vars:
        rside_string += rside_var + ", "

    line_start = code.rfind("\n", 0, location)
    line_end = code.find("\n", location)

    line = code[line_start:location] + '\033[4m' + code[location:location + 2] + '\033[0m' + code[location + 2: line_end]
    # print(line + "\nLeft Side: " + lside + "; Right Side: " + rside_string)
    # print("")

print("-------------------")
print("Final dependencies:")

for var in dependencies:
    print(var + ": ", end = "")
    for dep in dependencies[var]:
        print(dep + ", ", end = "")
    print()

graph = nx.DiGraph()
for var in dependencies:
    graph.add_node(var)

for var in dependencies:
    for dep in dependencies[var]:
        if var != dep:
            graph.add_edge(var, dep)

#pos = nx.drawing.layout.spring_layout(graph, k = 0.6)
#pos = nx.drawing.layout.planar_layout(graph)
#pos = nx.drawing.layout.fruchterman_reingold_layout(graph)
pos = nx.drawing.layout.circular_layout(graph)
nx.draw(graph, with_labels=True, pos=pos, node_color="#BBBBFF")
plt.savefig(filename + ".png")
plt.show()