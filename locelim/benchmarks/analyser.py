# manual analysis of bluetooth benchmark
import time
from typing import Dict, List, Tuple

import stormpy as sp
from stormpy.utility.utility import Z3SmtSolver, SmtCheckResult

import unfolder
from locelim.datastructures.PCFP import PCFP
from locelim.datastructures.command import Command
from locelim.datastructures.util import are_locs_equal


# a small hack to print variables/expressions right
sp.storage.Variable.__repr__ = lambda self: self.name
sp.Expression.__repr__ = lambda self: str(self)

from locelim.datastructures.update import Update


def bluetooth_manual_simplification():
    prism_program = sp.parse_prism_program("originals/brp.prism")
    prism_props = sp.parse_properties_for_prism_program("R=? [ C ]", prism_program)  # These props probably don't make sense for bluetooth?
    jani_model, jani_props = prism_program.to_jani(prism_props)
    jani_model = jani_model.flatten_composition()

    # start simplifying the model, convert to pcfp first
    # here we leave undef constants undefined
    orig_pcfp = PCFP.from_jani(jani_model)

    # orig_pcfp.ini

    mgr: sp.ExpressionManager = orig_pcfp.get_manager()

    pcfp = analyse_potential_unfolds(orig_pcfp)

    print(pcfp.to_prism_string())

    # model = sp.build_model(prism_program, prism_props)
    # result = sp.model_checking(model, prism_props[0])
    # initial_state = model.initial_states[0]
    # print("number of states: {}".format(len(model.states)))
    # print(result.at(initial_state))


def analyse_potential_unfolds(orig_pcfp):
    vars = [init_value for init_value in orig_pcfp.initial_values]
    for var in vars:
        pcfp = orig_pcfp.copy()

        min_bound, max_bound = orig_pcfp.int_variables_bounds[var]
        min_bound: sp.Expression
        max_bound: sp.Expression

        if min_bound.contains_variables():
            print("Skipping " + str(var) + " because min_bound is not constant.")
            continue
        if max_bound.contains_variables():
            print("Skipping " + str(var) + " because max_bound is not constant.")
            continue

        min_value, max_value = min_bound.evaluate_as_int(), max_bound.evaluate_as_int()
        range: int = 1 + max_value - min_value

        if range > 15:
            print("Skipping " + str(var) + " because range too large (" + str(range) + ")")
            continue

        start = time.time()
        pcfp.unfold(var)
        end = time.time()
        print("Unfolded " + str(var) + " (range: " + str(range) + ") in " + str(end - start) + "s.")
        analyse_locations(pcfp)
    return pcfp


def analyse_locations(pcfp, silent=False, max_new_transitions=100):
    best_unfold = None
    min_unfold_transitions = max_new_transitions  # Adjusts the cutoff after which eliminating a location is considered worse than keeping it
    initial_loc = pcfp.get_initial_location()
    for loc in pcfp.get_locs():
        if not silent:
            print("  Location " + str(loc))

        if are_locs_equal(initial_loc, loc):
            if not silent:
                print("  Location is initial. Skipping location.")
            continue

        incoming_guards_and_assigs = []
        for cmd in pcfp.commands:
            for dest in cmd.destinations:
                if are_locs_equal(dest.target_loc, loc):
                    incoming_guards_and_assigs.append((cmd.guard, dest.update))

        if len(incoming_guards_and_assigs) == 0:
            if not silent:
                print("    No incoming transitions (?)")
            continue

        if not silent:
            print("    " + str(len(incoming_guards_and_assigs)) + " incoming transitions")

        outgoing_commands = pcfp.get_commands_with_source(loc)
        self_loops_reachable = 0
        self_loops_not_reachable = 0
        for cmd in outgoing_commands:
            cmd: Command
            for dest in cmd.destinations:
                dest: Command.Destination
                if are_locs_equal(dest.target_loc, loc):
                    reachable = is_loop_reachable(incoming_guards_and_assigs, cmd.guard, pcfp)
                    if not reachable:
                        if self_loops_not_reachable < 3 and not silent:
                            print("    Self-loop. Not reachable.")
                        self_loops_not_reachable += 1
                    else:
                        if self_loops_reachable < 3 and not silent:
                            print("    Self-loop. Reachable." + str(dest.update))
                        self_loops_reachable += 1

        if (self_loops_not_reachable >= 3 or self_loops_reachable >= 3) and not silent:
            print("    ... (total " + str(self_loops_not_reachable + self_loops_reachable) + ", " + str(self_loops_reachable) + " reachable)")
        if self_loops_reachable == 0:
            total_transitions = len(incoming_guards_and_assigs) * len(outgoing_commands)
            new_transitions = total_transitions - len(incoming_guards_and_assigs) - len(outgoing_commands)
            if new_transitions < min_unfold_transitions:
                min_unfold_transitions = new_transitions
                best_unfold = loc

            if not silent:
                print("    No reachable self loops found. Unfold possible. No. of new transitions: " + str(new_transitions))

    return best_unfold


def is_loop_reachable(incomings: List[Tuple[sp.Expression, Update]], loop_guard: sp.Expression, pcfp: PCFP):
    for (in_guard, in_update) in incomings:
        wp: sp.Expression = in_update.wp(loop_guard)
        if not wp.contains_variables() and not wp.evaluate_as_bool():
            continue

        guard = sp.Expression.And(in_guard, wp)
        guard: sp.Expression

        solver = Z3SmtSolver(guard.manager)
        solver.add(guard)
        for var in guard.get_variables():
            if var in pcfp._undef_constants:
                continue
            if not var in pcfp.int_variables_bounds:
                continue
            var: sp.Variable
            lower_bound = sp.Expression.Geq(var.get_expression(), pcfp.get_lower_bound(var))
            upper_bound = sp.Expression.Leq(var.get_expression(), pcfp.get_upper_bound(var))
            solver.add(lower_bound)
            solver.add(upper_bound)
        solver.push()
        if solver.check() != SmtCheckResult.Unsat:
            return True
    return False


if __name__ == "__main__":
    bluetooth_manual_simplification()
