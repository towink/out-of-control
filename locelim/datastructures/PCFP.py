from __future__ import annotations
from typing import Dict, Tuple
import logging

from stormpy.utility import Z3SmtSolver, SmtCheckResult

from locelim.datastructures.command import Command
from locelim.datastructures.util import *
from locelim.datastructures.update import AtomicUpdate, Assignment


# a probabilistic control flow program (a restricted form of jani program)
class PCFP:
    commands: [Command] = []

    # lower/upper bound for bounded integer variables only
    int_variables_bounds: Dict[sp.Variable, Tuple[sp.Expression, sp.Expression]] = {}

    # the boolean variables, they don't need bounds
    boolean_variables: [sp.Variable] = []

    # unique initial variable valuation for all variables
    initial_values: Dict[sp.Variable, sp.Expression] = {}

    # initial locations
    initial_locs: {object} = set()

    # all undefined constants, may appear in variable bounds, guards, probabilities, updates
    # TODO probably better to refer to orig jani for this
    _undef_constants: [sp.Variable] = []

    # jani model this PCFP was originally constructed from, is used to export to jani again
    original_jani: sp.JaniModel = None

    def __init__(self, original_jani: sp.JaniModel):
        self.commands = []
        self.int_variables_bounds = {}
        self.initial_values = {}
        self.initial_locs = set()
        self._undef_constants = []
        self.original_jani = original_jani

    def copy(self):
        new_pcfp = PCFP(self.original_jani)
        new_pcfp.commands = list.copy(self.commands)
        new_pcfp.int_variables_bounds = dict.copy(self.int_variables_bounds)
        new_pcfp.initial_values = dict.copy(self.initial_values)
        new_pcfp.initial_locs = set.copy(self.initial_locs)
        new_pcfp._undef_constants = list.copy(self._undef_constants)
        return new_pcfp

    def get_lower_bound(self, var: sp.Variable) -> sp.Expression:
        return self.int_variables_bounds[var][0]

    def get_upper_bound(self, var: sp.Variable) -> sp.Expression:
        return self.int_variables_bounds[var][1]

    def count_destinations(self):
        return sum([cmd.count_destinations() for cmd in self._commands])

    def unfold(self, var: sp.Variable):
        substitutions = [{var: val} for val in self.get_values_for_variable(var)]
        logging.info("unfolding {} will create {} new locations".format(var.name, (len(substitutions) - 1) * len(self.get_locs())))
        new_commands = []
        for subst in substitutions:
            new_commands += filter(
                lambda cmd: not cmd.is_guard_false(),  # only consider commands where guard has not evaluated to false
                [cmd.substitute(subst) for cmd in self.commands]
            )
        self.commands = new_commands
        self.eliminate_unreachable()
        logging.info("finished unfolding, there are now {} locations".format(len(self.get_locs())))

    # eliminates specified transition, see paper
    def eliminate_transition(self, cmd: Command, dest: Command.Destination, silent=False):
        next_cmds = self.get_commands_with_source(dest.target_loc)
        guards = [sp.Expression.And(cmd.guard, dest.update.wp(next_cmd.guard)).simplify() for next_cmd in next_cmds]
        probabilities_list = [
            [d.probability for d in cmd.destinations if d is not dest]
            # reuse wp here to substitute variables in probability expression
            + [sp.Expression.Multiply(dest.probability, dest.update.wp(next_dest.probability)).simplify() for next_dest in
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
                if not silent:
                    print("smt solver returned UNSAT")
                continue
            destinations = [Command.Destination(p, u, t) for p, u, t in zip(probabilities, updates, targets)]
            self._commands.append(Command(cmd.source_loc, guard, destinations))
        # finally remove the input command
        self._commands.remove(cmd)

    # if loc has no self-loops then it will be unreachable after applying this function
    def eliminate_loc(self, loc, silent=False):
        to_eliminate = self.get_destinations_with_target(loc)
        while to_eliminate:
            cmd, dest = to_eliminate.pop()  # only need one item of to_elimnate, so could be optimized
            if not silent:
                print("eliminate transition {} ---{}---> {}".format(cmd.source_loc, cmd.guard, dest))
            self.eliminate_transition(cmd, dest, silent)
            to_eliminate = self.get_destinations_with_target(loc)
        for cmd in self.get_commands_with_source(loc):
           self._commands.remove(cmd)

    def eliminate_unreachable(self):
        #reachable = [self.get_initial_location()]
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
        for cmd in self.commands:
            if is_in_reachable(cmd.source_loc):
                new_commands.append(cmd)

        logging.info("{} unreachable locations were removed".format(len(self.get_locs()) - len(reachable)))

        self.commands = new_commands

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

    # the locations that have no self loops, are not possibly initial or final
    def get_eliminable_locs(self, target_predicate: sp.Expression) -> []:
        result = []
        # I have tried to not create a new solver in each iteration but had difficulties with that
        for loc in self.get_locs_without_selfloops():
            goal_pred_loc_substituted = target_predicate.substitute(loc).simplify()
            solver = Z3SmtSolver(self.original_jani.expression_manager)
            solver.add(goal_pred_loc_substituted)
            solver.push()
            check_res = solver.check()
            if not self.is_loc_possibly_initial(loc) and check_res == SmtCheckResult.Unsat:
                result.append(loc)
        return result

    def get_commands_without_selfloops(self):
        return [cmd for cmd in self._commands if not cmd.has_selfloop()]

    def get_commands_with_source(self, source_loc):
        return list(filter(
            lambda cmd: are_locs_equal(source_loc, cmd.source_loc),
            self._commands
        ))

    def get_destinations_with_target(self, target_loc):
        result = []
        for cmd in self._commands:
            result += [(cmd, dest) for dest in cmd.destinations if are_locs_equal(dest.target_loc, target_loc)]
        return result

    def get_commands_with_nop_selfloop(self):
        return [cmd for cmd in self._commands if cmd.has_nop_selfloop() and len(cmd.destinations) > 1]

    def eliminate_nop_selfloops(self):
        for cmd in self.get_commands_with_nop_selfloop():
            if len(cmd.destinations) < 2:
                continue
            new_destinations = []
            for dest in cmd.destinations:
                if not dest.update.is_nop():
                    new_destinations.append(dest)
            cmd._destinations = new_destinations

    def is_loc_possibly_initial(self, loc) -> bool:
        for var in loc:
            if exp_to_primitive_type(loc[var]) != exp_to_primitive_type(self.initial_values[var]):
                return False
        return True

    def remove_unreachable_locs(self):
        raise NotImplementedError

    @property
    def commands(self):
        return self._commands

    def get_manager(self):
        return self.original_jani.expression_manager

    def add_command(self, cmd: Command):
        self.commands.append(cmd)

    # construct a PCFP object from a jani model
    @classmethod
    def from_jani(cls, jani_model: sp.JaniModel):
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

        # commands
        for edge in automaton.edges:
            edge: sp.JaniEdge
            #
            if len(automaton.locations) == 1:
                source_loc = {}  # if there is a unique location in jani then call it empty dict
            else:
                raise Exception("jani model must have a unique location")
                # source_loc = automaton.locations[edge.source_location_index]
            guard = edge.guard
            destinations = []
            for dest in edge.destinations:
                if len(automaton.locations) == 1:
                    target_loc = {}
                else:
                    # target_loc = automaton.locations[edge.target_location_index]
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
            res += "const int {};\n".format(const.name)

        res += "module autogenerated\n"

        for var in self.int_variables_bounds:
            res += "\t{}: [{}..{}] init {};\n"\
                .format(var.name, self.get_lower_bound(var), self.get_upper_bound(var), self.initial_values[var])

        for var in self.boolean_variables:
            res += "\t{}: bool init {};\n".format(var.name, self.initial_values[var])

        for cmd in self._commands:
            res += "\t{}\n".format(cmd.to_prism_string())

        res += "endmodule"
        return res

    # builds a JaniModel from this PCFP instance
    def to_jani(self) -> sp.JaniModel:
        # construct resulting jani model using the original jani model
        if self.original_jani is None:
            raise Exception("can only export to jani if PCFP was constructed with from_jani(...)")
        jani_model: sp.JaniModel = self.original_jani
        automaton = sp.JaniAutomaton("from PCFP", jani_model.automata[0].location_variable)

        # set (undefined) constants, remove old first
        # constants_in_orig_jani = [constant.name for constant in jani_model.constants]
        # for constant in constants_in_orig_jani:
        #     jani_model.remove_constant(constant)
        # for constant in self._undef_constants:
        #     # add_constant automatically sets has_undefined_constants to true
        #     jani_constant = sp.JaniConstant(constant.name, constant)
        #     jani_model.add_constant(jani_constant)

        # convert location set to list to assign (arbitrary) indices
        location_list = list(self.locations())

        # locations
        # use __str__ of PCFP location object as name
        for loc in self.locations():
            name = str(loc)
            assignments = sp.JaniOrderedAssignments([])
            automaton.add_location(sp.JaniLocation(name, assignments))

        # initial locations
        for initial_loc in self.initial_locs:
            initial_loc_index = location_list.index(initial_loc)
            automaton.add_initial_location(initial_loc_index)

        # commands/edges
        for cmd in self.commands:
            cmd: Command
            source_loc_index = location_list.index(cmd.source_loc)
            # for each edge we need a template edge that contains guard and destinations
            template_edge = sp.JaniTemplateEdge(cmd.guard)
            destinations_with_probabilities = []

            for dest in cmd.destinations:
                target_loc_index = location_list.index(dest.target_loc)
                destinations_with_probabilities.append((target_loc_index, dest.probability))
                assignments = sp.JaniOrderedAssignments([])
                if not isinstance(dest.update, AtomicUpdate):
                    raise NotImplementedError("transformation to jani not yet implemented for chained updates")
                for asg in dest.update._parallel_asgs:
                    assignments.add(sp.JaniAssignment(asg.lhs, asg.rhs))
                template_edge.add_destination(sp.JaniTemplateEdgeDestination(assignments))

            edge = sp.JaniEdge(source_loc_index, 0, None, template_edge, destinations_with_probabilities)
            automaton.add_edge(edge)

        # finally register the new automaton with the jani model and finalize
        jani_model.replace_automaton(0, automaton)
        jani_model.finalize()
        if not jani_model.check_valid():
            logging.warning("exported jani model is not valid")
        return jani_model

    @commands.setter
    def commands(self, value):
        self._commands = value
