# manual analysis of nand benchmark

# property "P=? [ F s=4 & z/N<0.1 ]"

import stormpy as sp

from locelim.datastructures.PCFP import PCFP

from locelim.interactive import *

# a small hack to print variables/expressions right
# sp.storage.Variable.__repr__ = lambda self: self.name
# sp.Expression.__repr__ = lambda self: str(self)


def transitions_count(model):
    res = 0
    for state in model.states:
        for action in state.actions:
            res += len(action.transitions)
    return res


def nand_manual_simplification():
    prism_program = sp.parse_prism_program("originals/nand.prism")
    #prism_props = sp.parse_properties_for_prism_program("P=? [ F s=4 & z/N<0.1 ]", prism_program)
    jani_model, jani_props = prism_program.to_jani([])
    # jani_model = jani_model.flatten_composition()


    prism_program: sp.PrismProgram

    jani_model:sp.JaniModel
    mgr = jani_model.expression_manager
    N = jani_model.get_constant("N").expression_variable
    K = jani_model.get_constant("K").expression_variable

    constant_vals = [
        {N: mgr.create_integer(20), K: mgr.create_integer(2)}
    ]

    for constant_val in constant_vals:
        print(constant_val)
        property_str = "P=? [ F s=4 & z/{}<0.1 ]".format(constant_val[N])
        property = sp.parse_properties_for_jani_model(property_str, jani_model)
        jani_model_const_def = jani_model.define_constants(constant_val)
        model = sp.build_model(jani_model_const_def, property)
        result = sp.model_checking(model, property[0])
        initial_state = model.initial_states[0]
        print("number of states: {}".format(len(model.states)))
        print("number of transitions: {}".format(transitions_count(model)))
        print(result.at(initial_state))

    # start simplifying the model, convert to pcfp first
    # here we leave undef constants undefined
    pcfp = PCFP.from_jani(jani_model)

    mgr: sp.ExpressionManager = pcfp.get_manager()
    s = mgr.get_variable("s")
    x = mgr.get_variable("x")
    y = mgr.get_variable("y")
    pcfp.unfold(s)
    # pcfp.unfold(x)
    # pcfp.unfold(y)

    loc_to_eliminate = [
        {s: mgr.create_integer(1)},  # eliminate s=1
        {s: mgr.create_integer(2)},  # eliminate s=1
        {s: mgr.create_integer(3)},  # eliminate s=1
    ]

    [print(cmd) for cmd in pcfp.commands]

    for loc in loc_to_eliminate:
        print("eliminating location {} ...".format(loc))
        pcfp.eliminate_loc(loc)
        [print(cmd) for cmd in pcfp.commands]

    # pcfp.unfold(x)
    # pcfp.unfold(y)

    simplified_prism_str = pcfp.to_prism_string()
    print(simplified_prism_str)
    with open("tmp.prism", "w") as f:
        f.write(simplified_prism_str)
    simplified_prism = sp.parse_prism_program("tmp.prism")
    jani_model, _ = simplified_prism.to_jani([])
    jani_model.remove_constant("M")
    jani_model.remove_constant("perr")
    jani_model.remove_constant("prob1")

    mgr = jani_model.expression_manager
    N = jani_model.get_constant("N").expression_variable
    K = jani_model.get_constant("K").expression_variable

    constant_vals = [
        {N: mgr.create_integer(20), K: mgr.create_integer(2)}
    ]

    for constant_val in constant_vals:
        print(constant_val)
        property_str = "P=? [ F s=4 & z/{}<0.1 ]".format(constant_val[N])
        property = sp.parse_properties_for_jani_model(property_str, jani_model)
        jani_model_const_def = jani_model.define_constants(constant_val)
        model = sp.build_model(jani_model_const_def, property)
        result = sp.model_checking(model, property[0])
        initial_state = model.initial_states[0]
        print("number of states: {}".format(len(model.states)))
        print("number of transitions: {}".format(transitions_count(model)))
        print(result.at(initial_state))



    # model = sp.build_model(prism_program, prism_props)
    # result = sp.model_checking(model, prism_props[0])
    # initial_state = model.initial_states[0]
    # print("number of states: {}".format(len(model.states)))
    # print(result.at(initial_state))

if __name__ == "__main__":
    #nand_manual_simplification()

    # comment out to disable logging
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

    load_model("originals/nand.prism")
    show_model_constants()
    set_property("P=? [ F s=4 & z/N<0.1 ]")
    def_model_constants({'N': 10, 'K': 10})

    res_orig = check_orig_model()

    unfold("s")
    eliminate({"s": 2})
    eliminate({"s": 3})
    eliminate({"s": 1})
    #eliminate_all()
    show_stats()
    show_as_prism()

    model = session().build_model()
    session().check_model()
    print(model)
