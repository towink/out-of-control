# manual analysis of nand benchmark

import stormpy as sp

from datastructures.PCFP import PCFP
from datastructures.command import Command


# a small hack to print variables/expressions right
sp.storage.Variable.__repr__ = lambda self: self.name
sp.Expression.__repr__ = lambda self: str(self)


def nand_manual_simplification():
    prism_program = sp.parse_prism_program("originals/nand.prism")
    prism_props = sp.parse_properties_for_prism_program("R=? [ C ]", prism_program)
    jani_model, jani_props = prism_program.to_jani(prism_props)
    # jani_model = jani_model.flatten_composition()

    #jani_model.define_constants()
    # model = sp.build_model(prism_program, prism_props)
    # result = sp.model_checking(model, prism_props[0])
    # initial_state = model.initial_states[0]
    # print("number of states: {}".format(len(model.states)))
    # print(result.at(initial_state))

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

    loc_to_eliminate = {
        s: mgr.create_integer(1)  # eliminate s=1
    }

    for loc in [loc_to_eliminate]:
        print("eliminating location {} ...".format(loc))
        pcfp.eliminate_loc(loc)
        [print(cmd) for cmd in pcfp.commands]

    print(pcfp.to_prism_string())

    # model = sp.build_model(prism_program, prism_props)
    # result = sp.model_checking(model, prism_props[0])
    # initial_state = model.initial_states[0]
    # print("number of states: {}".format(len(model.states)))
    # print(result.at(initial_state))

if __name__ == "__main__":
    nand_manual_simplification()
