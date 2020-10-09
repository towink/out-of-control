from __future__ import annotations

import time
from typing import Dict, Tuple
import logging

from stormpy.utility import Z3SmtSolver, SmtCheckResult

from locelim.datastructures.command import Command
from locelim.datastructures.util import *
from locelim.datastructures.update import AtomicUpdate, Assignment


class PCFP:
    """Represents a probabilistic control flow program"""

    # private fields

    # the set of location-guided commands, contain the locations
    _commands: [Command] = []

    # lower/upper bound for bounded integer variables only
    int_variables_bounds: Dict[sp.Variable, Tuple[sp.Expression, sp.Expression]] = {}

    # the boolean variables, they don't need bounds
    boolean_variables: [sp.Variable] = []

    # unique initial variable valuation for all variables
    initial_values: Dict[sp.Variable, sp.Expression] = {}

    # initial locations
    initial_locs: {object} = set()

    # all undefined constants, may appear in variable bounds, guards, probabilities, updates
    _undef_constants: [sp.Variable] = []
    _undef_constants_types: Dict[sp.Variable, sp.ExpressionType] = []

    # jani model this PCFP was originally constructed from, is used to export to jani again
    original_jani: sp.JaniModel = None

    # getters/setters

    @property
    def commands(self):
        return self._commands

    # constructors

    def __init__(self, original_jani: sp.JaniModel):
        self._commands = []
        self.int_variables_bounds = {}
        self.boolean_variables = []
        self.initial_values = {}
        self.initial_locs = set()
        self._undef_constants = []
        self._undef_constants_types = dict()
        self.original_jani = original_jani

    def copy(self):
        new_pcfp = PCFP(self.original_jani)
        new_pcfp._commands = list.copy(self._commands)
        new_pcfp.int_variables_bounds = dict.copy(self.int_variables_bounds)
        new_pcfp.initial_values = dict.copy(self.initial_values)
        new_pcfp.initial_locs = set.copy(self.initial_locs)
        new_pcfp._undef_constants = list.copy(self._undef_constants)
        new_pcfp._undef_constants_types = dict.copy(self._undef_constants_types)
        return new_pcfp

    @classmethod
    def from_jani(cls, jani_model: sp.JaniModel):
        """Constructs a PCFP from a jani model"""
        if not jani_model.check_valid():
            logging.warning("provided jani_model is not valid")
        if len(jani_model.automata) > 1:
            logging.warning("jani models with multiple automata are not supported, ignoring all but first")
        automaton: sp.JaniAutomaton = jani_model.automata[0]
        new_instance = PCFP(jani_model)

        # variable bounds
        for jani_var in jani_model.global_variables:
            var = jani_var.expression_variable
            new_instance.initial_values[var] = jani_var.init_expression
            if type(jani_var) is sp.JaniBoundedIntegerVariable:
                lower_bound = jani_var.lower_bound
                upper_bound = jani_var.upper_bound
                new_instance.int_variables_bounds[var] = (lower_bound, upper_bound)
            elif var.has_boolean_type():
                new_instance.boolean_variables.append(var)
            else:
                logging.warning("unsupported variable: {}".format(jani_var.name))

        # undefined constants
        for constant in jani_model.constants:
            # the defined constants (e.g. const int N=5 in prism) are substituted in jani model, so ignore them
            if not constant.defined:
                new_instance._undef_constants.append(constant.expression_variable)
                new_instance._undef_constants_types[constant.expression_variable] = constant.type

        # commands
        for edge in automaton.edges:
            edge: sp.JaniEdge
            if len(automaton.locations) == 1:
                source_loc = {}  # nothing unfolded yet -> empty dict
            else:
                raise Exception("jani model must have a unique location")
            guard = edge.guard
            destinations = []
            for dest in edge.destinations:
                if len(automaton.locations) == 1:
                    target_loc = {}
                else:
                    raise Exception("jani model must have a unique location")
                probability = dest.probability
                update = AtomicUpdate()
                for asg in dest.assignments:
                    update.add_assignment(Assignment(asg.variable.expression_variable, asg.expression))
                destinations.append(Command.Destination(probability, update, target_loc))
            cmd = Command(source_loc, guard, destinations)
            new_instance.add_command(cmd)

        # initial locations
        for index in automaton.initial_location_indices:
            new_instance.initial_locs.add(automaton.locations[index])

        return new_instance

    # public functions

    def add_command(self, cmd: Command):
        self._commands.append(cmd)

    def is_unfoldable(self, var: sp.Variable):
        for cmd in self._commands:
            for dest in cmd.destinations:
                subst_map = dest.update.to_subst_map()
                if var in subst_map:
                    subst_term: sp.Expression = subst_map[var]
                    variables = subst_term.get_variables()
                    if len(variables) > 1 or (len(variables) == 1 and next(iter(variables)) != var):
                        logging.info("{} is not unfoldable as it is assigned the value \"{}\"".format(
                            str(var), str(subst_term)
                        ))
                        return False
        return True

    def unfold(self, var: sp.Variable):
        """Unfolds the given variable into the location space"""
        if not self.is_unfoldable(var):
            raise Exception("The variable cannot be unfolded")

        substitutions = [{var: val} for val in self.get_values_for_variable(var)]
        logging.info("unfolding {} will create {} new locations"
                     .format(var.name, (len(substitutions) - 1) * len(self.get_locs())))
        new_commands = []
        for subst in substitutions:
            new_commands += filter(
                lambda cmd: not cmd.is_guard_false(),  # only consider commands where guard has not evaluated to false
                [cmd.substitute(subst) for cmd in self._commands]
            )
        self._commands = new_commands
        self.eliminate_unreachable()
        logging.info("finished unfolding, there are now {} locations".format(len(self.get_locs())))

    def eliminate_transition(self, cmd: Command, dest: Command.Destination):
        # eliminates specified transition, see paper
        next_cmds = self.get_commands_with_source(dest.target_loc)
        # step 1 - build and analyse guards
        guards = [sp.Expression.And(cmd.guard, dest.update.wp(next_cmd.guard)).simplify() for next_cmd in next_cmds]
        # step 2 - build destinations, updates, targets
        probabilities_list = [
            [d.probability for d in cmd.destinations if d is not dest]
            # reuse wp here to substitute variables in probability expression
            + [sp.Expression.Multiply(dest.probability, dest.update.wp(next_dest.probability)).simplify() for next_dest
               in
               next_cmd.destinations]
            for next_cmd in next_cmds
        ]
        updates_list = [
            [d.update for d in cmd.destinations if d is not dest]
            + [next_dest.update.after(dest.update) for next_dest in next_cmd.destinations]
            for next_cmd in next_cmds
        ]
        targets_list = [
            [d.target_loc for d in cmd.destinations if d is not dest]
            + [next_dest.target_loc for next_dest in next_cmd.destinations]
            for next_cmd in next_cmds
        ]
        # step 3 - build the new commands
        for guard, probabilities, updates, targets in zip(guards, probabilities_list, updates_list, targets_list):
            # check if guard is SAT

            solver = Z3SmtSolver(guard.manager)
            guard: sp.Expression
            solver.add(guard)
            for var in guard.get_variables():
                if var in self._undef_constants or var.has_boolean_type():
                    continue
                if not var in self.int_variables_bounds:
                    continue
                var: sp.Variable
                lower_bound = sp.Expression.Geq(var.get_expression(), self.get_lower_bound(var))
                upper_bound = sp.Expression.Leq(var.get_expression(), self.get_upper_bound(var))
                solver.add(lower_bound)
                solver.add(upper_bound)
            solver.push()
            if solver.check() == SmtCheckResult.Unsat:
                # if not silent:
                #    print("smt solver returned UNSAT")
                continue
            destinations = [Command.Destination(p, u, t) for p, u, t in zip(probabilities, updates, targets)]
            self._commands.append(Command(cmd.source_loc, guard, destinations))
        # finally remove the input command
        self._commands.remove(cmd)

    # if loc has no self-loops then it will be unreachable after applying this function
    def eliminate_loc(self, loc):
        logging.info("eliminating {}".format(loc))
        t_start = time.time()
        to_eliminate = self.get_destinations_with_target(loc, include_selfloops=False)
        while to_eliminate:
            cmd, dest = to_eliminate.pop()  # only need one item of to_eliminate, so could be optimized
            logging.debug("eliminate transition {} ---{}---> {}".format(cmd.source_loc, cmd.guard, dest))
            self.eliminate_transition(cmd, dest)
            to_eliminate = self.get_destinations_with_target(loc, include_selfloops=False)
        for cmd in self.get_commands_with_source(loc):
            self._commands.remove(cmd)
        t_end = time.time()
        logging.info("elimination took {}s".format(t_end - t_start))

    def remove_duplicate_cmds(self):
        dupls = len(self._commands) * [False]
        for i in range(len(self._commands)):
            if dupls[i]:
                continue
            for j in range(i - 1):
                if self._commands[i].is_equal_except_guard(self._commands[j]):
                    dupls[j] = True
                    guard_i, guard_j = self._commands[i].guard, self._commands[j].guard
                    joint_guard: sp.Expression = sp.Expression.Or(guard_i, guard_j)
                    joint_guard = joint_guard.simplify()
                    self._commands[i].guard = joint_guard

        self._commands = [cmd for i, cmd in enumerate(self._commands) if not dupls[i]]

        removed = len([() for i, dup in enumerate(dupls) if dup])
        logging.info("removed {} duplicate commands".format(removed))

    def eliminate_unreachable(self):
        # TODO this seems to be quite slow ...
        # reachable = [self.get_initial_location()]
        reachable = [loc for loc in self.get_locs() if self.is_loc_possibly_initial(loc)]

        def is_in_reachable(loc):
            for r in reachable:
                if are_locs_equal(r, loc):
                    return True
            return False

        current_index = 0
        while current_index < len(reachable):
            cmds = self.get_commands_with_source(reachable[current_index])

            for cmd in cmds:
                for dest in cmd.destinations:
                    if not is_in_reachable(dest.target_loc):
                        reachable.append(dest.target_loc)

            current_index += 1

        new_commands = []
        for cmd in self._commands:
            if is_in_reachable(cmd.source_loc):
                new_commands.append(cmd)

        logging.info("{} unreachable locations were removed".format(len(self.get_locs()) - len(reachable)))

        self._commands = new_commands

    def eliminate_nop_selfloops(self):
        counter = 0  # count how many are eliminated
        for cmd in self._commands:
            selfloops = cmd.get_nop_selfloops()
            if len(cmd.destinations) == len(selfloops) or len(selfloops) == 0:
                # do not consider cmds that either have only nop self loops or none at all
                continue
            counter += len(selfloops)  # count how many are eliminated
            new_destinations = [dest for dest in cmd.destinations if dest not in selfloops]
            for dest in new_destinations:
                for loop in selfloops:
                    dest.probability = dest.probability * 1 / (1 - loop.probability)
            cmd._destinations = new_destinations
        logging.info("removed {} nop-selfloops".format(counter))

    def get_lower_bound(self, var: sp.Variable) -> sp.Expression:
        return self.int_variables_bounds[var][0]

    def get_upper_bound(self, var: sp.Variable) -> sp.Expression:
        return self.int_variables_bounds[var][1]

    def count_destinations(self):
        return sum([cmd.count_destinations() for cmd in self._commands])

    def eliminate_unsatisfiable_commands(self):
        counter = 0
        for loc in self.get_locs():
            if self.is_loc_possibly_initial(loc):
                continue

            incoming_dests = self.get_destinations_with_target(loc)
            outgoing_commands = self.get_commands_with_source(loc)

            for outgoing in outgoing_commands:
                outgoing: Command
                reachable = False
                for (cmd, dest) in incoming_dests:
                    cmd: Command
                    dest: Command.Destination
                    wp_out = dest.update.wp(outgoing.guard)
                    total_guard: sp.Expression = sp.Expression.And(cmd.guard, wp_out)

                    if not total_guard.contains_variables():
                        if total_guard.evaluate_as_bool():
                            reachable = True
                            break
                        else:
                            continue

                    solver = Z3SmtSolver(total_guard.manager)
                    solver.add(total_guard)
                    for var in total_guard.get_variables():
                        var: sp.Variable
                        if var in self._undef_constants or not var in self.int_variables_bounds:
                            continue
                        solver.add(sp.Expression.Geq(var.get_expression(), self.get_lower_bound(var)))
                        solver.add(sp.Expression.Leq(var.get_expression(), self.get_upper_bound(var)))
                    solver.push()
                    if solver.check() != SmtCheckResult.Unsat:
                        reachable = True
                        break
                if not reachable:
                    self.commands.remove(outgoing)
                    counter += 1
        logging.info("removed {} unsatisfiable commands".format(counter))

    def get_initial_location(self):
        locs = self.get_locs()
        for loc in locs:
            is_initial = True
            for var in loc:
                loc_val: sp.Expression = loc[var]
                init_val: sp.Expression = self.initial_values[var]
                eq = sp.Expression.Eq(loc_val, init_val)
                if not eq.evaluate_as_bool():
                    is_initial = False
                    break
            if is_initial:
                return loc
        raise Exception("Could not find initial location. Perhaps it was eliminated?")

    # list of all values (as sp.Expression) that the given variable (int/bool) can take
    # will not work if undefined constants are in bounds
    def get_values_for_variable(self, var: sp.Variable) -> [sp.Expression]:
        exp_mgr: sp.ExpressionManager = self.get_manager()
        if var.has_integer_type():
            if var not in self.int_variables_bounds:
                raise Exception("no bounds known for int variable {}".format(var.name))
            bounds = self.int_variables_bounds[var]  # tuple of lower/upper bound
            # check if variable bounds depend on undefined constants
            if bounds[0].contains_variables() or bounds[1].contains_variables():
                raise Exception("variable bounds contain constants")
            lower_bound: int = bounds[0].evaluate_as_int()
            upper_bound: int = bounds[1].evaluate_as_int()
            # both bounds are inclusive
            return [exp_mgr.create_integer(val) for val in range(lower_bound, upper_bound + 1)]
        elif var.has_boolean_type():
            return [exp_mgr.create_boolean(True), exp_mgr.create_boolean(False)]
        else:
            raise Exception("only int or boolean variables are supported")

    def get_locs(self):
        result = []
        for cmd in self._commands:
            if cmd.source_loc not in result:
                result.append(cmd.source_loc)
        return result

    def get_locs_without_selfloops(self):
        return [loc for loc in self.get_locs() if
                all(map(lambda cmd: not cmd.has_selfloop(), self.get_commands_with_source(loc)))]

    def is_loc_potential_goal(self, loc, goal_predicate):
        goal_pred_loc_substituted = goal_predicate.substitute(loc).simplify()
        solver = Z3SmtSolver(self.original_jani.expression_manager)
        solver.add(goal_pred_loc_substituted)
        solver.push()
        check_res = solver.check()
        if check_res == SmtCheckResult.Unsat:
            return False
        else:
            return True

    # the locations that have no self loops, are not possibly initial or final
    def get_eliminable_locs(self, goal_predicate: sp.Expression) -> []:
        result = []
        for loc in self.get_locs_without_selfloops():
            if not self.is_loc_possibly_initial(loc) and not self.is_loc_potential_goal(loc, goal_predicate):
                result.append(loc)
        return result

    def is_loc_sink_without_target(self, loc, goal_predicate):
        # all outgoing transitions are self loops and loc is no potential goal
        if self.is_loc_potential_goal(loc, goal_predicate):
            return False
        for cmd in self.get_commands_with_source(loc):
            # if some command at loc has a non self-loop transition then loc is no sink
            if not cmd.has_only_selfloops():
                return False
        return True

    def get_sink_locs_without_targets(self, goal_predicate):
        return [loc for loc in self.get_locs() if self.is_loc_sink_without_target(loc, goal_predicate)]

    def is_loc_lucky(self, loc):
        # loc is lucky if it does have self-loops but can be eliminated anyway (by eliminate(loc))
        cmds = self.get_commands_with_source(loc)
        selfloops = [cmd for cmd in cmds if cmd.has_selfloop()]
        if not selfloops:
            # if the location has no self loop at all then don't consider it
            return False
        ingoing = [(cmd, dest) for (cmd, dest) in self.get_destinations_with_target(loc)
                   if not are_locs_equal(cmd.source_loc, loc)]
        solver = Z3SmtSolver(self.get_manager())
        for cmd, dest in ingoing:
            for loop in selfloops:
                solver.reset()
                query = sp.Expression.And(cmd.guard, dest.update.wp(loop.guard))
                solver.add(query)
                solver.push()
                check_res = solver.check()
                if check_res != SmtCheckResult.Unsat:
                    # if some combination of self loop and ingoing transition is sat then we are not lucky
                    return False
        return True

    def get_lucky_locs(self):
        result = []
        for loc in self.get_locs():
            if self.is_loc_lucky(loc):
                result.append(loc)
        return result

    def get_commands_without_selfloops(self):
        return [cmd for cmd in self._commands if not cmd.has_selfloop()]

    def get_commands_with_source(self, source_loc):
        return list(filter(
            lambda cmd: are_locs_equal(source_loc, cmd.source_loc),
            self._commands
        ))

    def get_commands_with_target(self, target_loc):
        result = []
        for cmd in self._commands:
            for dest in cmd.destinations:
                if are_locs_equal(dest.target_loc, target_loc):
                    result.append(cmd)
                    break
        return result

    def get_destinations_with_target(self, target_loc, include_selfloops=True):
        result = []
        for cmd in self._commands:
            if not include_selfloops and are_locs_equal(cmd.source_loc, target_loc):
                continue
            result += [(cmd, dest) for dest in cmd.destinations if are_locs_equal(dest.target_loc, target_loc)]
        return result

    def estimate_elim_complexity_for_loc(self, loc):
        # an estimate for how complex eliminating the given loc would be
        return len(self.get_destinations_with_target(loc)) * len(self.get_commands_with_source(loc))

    def get_commands_with_nop_selfloop(self):
        return [cmd for cmd in self._commands if cmd.has_nop_selfloop() and len(cmd.destinations) > 1]

    def has_removable_nop_selfloops(self):
        # removable means that it is not the self loop on the sink
        raise NotImplementedError

    def is_loc_possibly_initial(self, loc) -> bool:
        for var in loc:
            if exp_to_primitive_type(loc[var]) != exp_to_primitive_type(self.initial_values[var]):
                return False
        return True

    def get_manager(self):
        return self.original_jani.expression_manager

    # type (dtmc or mdp) as string
    def get_model_type(self) -> str:
        if self.original_jani.model_type == sp.JaniModelType.DTMC:
            return "dtmc"
        elif self.original_jani.model_type == sp.JaniModelType.MDP:
            return "mdp"
        else:
            raise Exception("model type {} is not supported".format(self.original_jani.model_type))

    # converts this PCFP to a PRISM program as string
    def to_prism_string(self) -> str:
        res = "\n//AUTOGENERATED FILE FROM PCFP\n"

        res += self.get_model_type() + "\n"

        for const in self._undef_constants:
            type = self._undef_constants_types[const]
            type_str = ""
            if type.is_integer:
                type_str = "int"
            elif type.is_boolean:
                type_str = "bool"
            else:
                raise Exception("Unknown variable type")
            res += "const {} {};\n".format(type_str, const.name)

        res += "module autogenerated\n"

        for var in self.int_variables_bounds:
            res += "\t{}: [{}..{}] init {};\n" \
                .format(var.name, self.get_lower_bound(var), self.get_upper_bound(var), self.initial_values[var])

        for var in self.boolean_variables:
            res += "\t{}: bool init {};\n".format(var.name, self.initial_values[var])

        # for cmd in self._commands:
        #     res += "\t{}\n".format(cmd.to_prism_string())

        for loc in self.get_locs():
            cmds = self.get_commands_with_source(loc)
            for cmd in cmds:
                res += "\t{}\n".format(cmd.to_prism_string())

        res += "endmodule"
        return res

    def to_jani(self) -> sp.JaniModel:
        # builds a JaniModel from this PCFP instance
        raise NotImplementedError
        # # construct resulting jani model using the original jani model
        # if self.original_jani is None:
        #     raise Exception("can only export to jani if PCFP was constructed with from_jani(...)")
        # jani_model: sp.JaniModel = self.original_jani
        # automaton = sp.JaniAutomaton("from PCFP", jani_model.automata[0].location_variable)
        #
        # # set (undefined) constants, remove old first
        # # constants_in_orig_jani = [constant.name for constant in jani_model.constants]
        # # for constant in constants_in_orig_jani:
        # #     jani_model.remove_constant(constant)
        # # for constant in self._undef_constants:
        # #     # add_constant automatically sets has_undefined_constants to true
        # #     jani_constant = sp.JaniConstant(constant.name, constant)
        # #     jani_model.add_constant(jani_constant)
        #
        # # convert location set to list to assign (arbitrary) indices
        # location_list = list(self.locations())
        #
        # # locations
        # # use __str__ of PCFP location object as name
        # for loc in self.locations():
        #     name = str(loc)
        #     assignments = sp.JaniOrderedAssignments([])
        #     automaton.add_location(sp.JaniLocation(name, assignments))
        #
        # # initial locations
        # for initial_loc in self.initial_locs:
        #     initial_loc_index = location_list.index(initial_loc)
        #     automaton.add_initial_location(initial_loc_index)
        #
        # # commands/edges
        # for cmd in self._commands:
        #     cmd: Command
        #     source_loc_index = location_list.index(cmd.source_loc)
        #     # for each edge we need a template edge that contains guard and destinations
        #     template_edge = sp.JaniTemplateEdge(cmd.guard)
        #     destinations_with_probabilities = []
        #
        #     for dest in cmd.destinations:
        #         target_loc_index = location_list.index(dest.target_loc)
        #         destinations_with_probabilities.append((target_loc_index, dest.probability))
        #         assignments = sp.JaniOrderedAssignments([])
        #         if not isinstance(dest.update, AtomicUpdate):
        #             raise NotImplementedError("transformation to jani not yet implemented for chained updates")
        #         for asg in dest.update._parallel_asgs:
        #             assignments.add(sp.JaniAssignment(asg.lhs, asg.rhs))
        #         template_edge.add_destination(sp.JaniTemplateEdgeDestination(assignments))
        #
        #     edge = sp.JaniEdge(source_loc_index, 0, None, template_edge, destinations_with_probabilities)
        #     automaton.add_edge(edge)
        #
        # # finally register the new automaton with the jani model and finalize
        # jani_model.replace_automaton(0, automaton)
        # jani_model.finalize()
        # if not jani_model.check_valid():
        #     logging.warning("exported jani model is not valid")
        # return jani_model
