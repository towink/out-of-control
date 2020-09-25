# manual analysis of bluetooth benchmark
import time
from typing import Dict, List, Tuple

import stormpy as sp
from stormpy.utility.utility import Z3SmtSolver, SmtCheckResult

import unfolder
from locelim.datastructures.PCFP import PCFP
from locelim.datastructures.command import Command
from locelim.benchmarks.analyser import analyse_locations, analyse_potential_unfolds

# a small hack to print variables/expressions right
sp.storage.Variable.__repr__ = lambda self: self.name
sp.Expression.__repr__ = lambda self: str(self)

from locelim.datastructures.update import Update


def bluetooth_manual_simplification():
    prism_program: sp.PrismProgram = sp.parse_prism_program("originals/brp.prism")
    prism_props = sp.parse_properties_for_prism_program("P=? [ F s=5 ]",
                                                        prism_program)  # These props probably don't make sense for bluetooth?
    jani_model, jani_props = prism_program.to_jani(prism_props)
    jani_model = jani_model.flatten_composition()

    # start simplifying the model, convert to pcfp first
    # here we leave undef constants undefined
    pcfp = PCFP.from_jani(jani_model)

    mgr: sp.ExpressionManager = pcfp.get_manager()

    # prism_defined = prism_program.define_constants({mgr.get_variable("N"): mgr.create_integer(16),
    #                                 mgr.get_variable("MAX"): mgr.create_integer(2)})
    # model = sp.build_model(prism_defined, prism_props)
    # print("number of states: {}".format(len(model.states)))

    r = mgr.get_variable("r")
    s = mgr.get_variable("s")
    k = mgr.get_variable("k")
    l = mgr.get_variable("l")

    pcfp.unfold(r)
    pcfp.unfold(s)


    # locs_to_eliminate = [{r: mgr.create_integer(1), s: mgr.create_integer(i)} for i in range(1, 5)]

    print(str(len(pcfp.get_locs())) + " Locations after unfolding r and s")
    pcfp.eliminate_unreachable()
    print(str(len(pcfp.get_locs())) + " Locations after eliminating unreachable")
    eliminate_locations(41, pcfp, 100)
    print(str(len(pcfp.get_locs())) + " Locations after elimination")

    pcfp.unfold(k)
    print(str(len(pcfp.get_locs())) + " Locations after unfolding k")
    pcfp.eliminate_unreachable()
    print(str(len(pcfp.get_locs())) + " Locations after eliminating unreachable")
    eliminate_locations(len(pcfp.get_locs()) - 1, pcfp, 500)
    print(str(len(pcfp.get_locs())) + " Locations after elimination")

    pcfp.unfold(l)
    print(str(len(pcfp.get_locs())) + " Locations after unfolding l")
    pcfp.eliminate_unreachable()
    print(str(len(pcfp.get_locs())) + " Locations after eliminating unreachable")
    eliminate_locations(len(pcfp.get_locs()) - 1, pcfp, 5000)
    print(str(len(pcfp.get_locs())) + " Locations after elimination")



    # analyse_potential_unfolds(pcfp)

    # analyse_potential_unfolds(pcfp)

    # analyse_locations(pcfp)

    # pcfp.eliminate_nop_selfloops()

    # print(pcfp.to_prism_string())


def eliminate_locations(max_tries, pcfp, new_transition_cutoff):
    for i in range(max_tries):
        best_loc = analyse_locations(pcfp, silent=True, max_new_transitions=new_transition_cutoff)
        if best_loc is None:
            print(
                "No more locations can be eliminated (or eliminating more locations would create too many transitions")
            break

        print("Eliminating " + str(best_loc))
        pcfp.eliminate_loc(best_loc, silent=True)


if __name__ == "__main__":
    bluetooth_manual_simplification()
