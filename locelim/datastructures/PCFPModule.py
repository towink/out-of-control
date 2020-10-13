from __future__ import annotations

import time
from typing import Dict, Tuple, Generator
import logging

import networkx as nx

from stormpy.utility import Z3SmtSolver, SmtCheckResult

from locelim.datastructures.util import *
from locelim.datastructures.update import AtomicUpdate, Assignment
from locelim.datastructures import PCFPComposition


class CmdNode:
    """Node in a PCFP modules's graph that represents a command."""
    action_label: str
    guard: sp.Expression

    def __init__(self, action_label: str, guard: sp.Expression):
        self.action_label = action_label
        self.guard = guard


class Location:
    """Node in a PCFP modules's graph that represents a location."""
    val_map: Dict[sp.Variable, sp.Expression] = {}

    @property
    def is_empty(self) -> bool:
        return self.val_map == {}

    def extend(self, substitutions: Dict[sp.Variable, sp.Expression]) -> Location:
        """Extends this location with the given variable substitutions (overwrites existing vals)."""
        result = Location()
        result.val_map = self.val_map.copy()
        for var, val in substitutions.items():
            result.val_map[var] = val
        return result

    def is_initial(self, initial_values) -> bool:
        """Determines if this location is initial for the given initial valuation."""
        for var in self.val_map:
            if exp_to_primitive_type(self.val_map[var]) != exp_to_primitive_type(initial_values[var]):
                return False
        return True

    def is_potential_goal(self, goal_predicate: sp.Expression) -> bool:
        """If this returns false, then the location is no pontential goal for sure."""
        goal_pred_loc_substituted = goal_predicate.substitute(self.val_map).simplify()
        if not goal_pred_loc_substituted.contains_variables():
            return goal_pred_loc_substituted.evaluate_as_bool()
        # TODO this might be too crude
        return True
        # # there are
        # solver = Z3SmtSolver(self.original_jani.expression_manager)
        # solver.add(goal_pred_loc_substituted)
        # solver.push()
        # check_res = solver.check()
        # if check_res == SmtCheckResult.Unsat:
        #     return False
        # else:
        #     return True

    def to_prism_string(self, as_update=False):
        prime = ""
        if as_update:
            prime = "'"
        return "&".join((f"({var}{prime} = {val})" for var, val in self.val_map.items()))

    def __eq__(self, other: Location):
        if len(self.val_map) != len(other.val_map):
            return False
        if self.val_map.keys() != other.val_map.keys():
            return False
        return all(
            (exp_to_primitive_type(self.val_map[v]) == exp_to_primitive_type(other.val_map[v]) for v in self.val_map))

    def __hash__(self):
        # take hash of tuple of assigned values, as string, int/bool tuples
        return hash(frozenset(((var.name, exp_to_primitive_type(val)) for var, val in self.val_map.items())))

    def __str__(self):
        return str(self.val_map)

    def __repr__(self):
        return str(self)


class Command:
    """This class is only used for printing so far, is not part of data structure."""
    source_loc: Location
    action_label: str
    guard: sp.Expression
    destinations: [(sp.PrismUpdate, Location)]

    def __init__(self, source_loc, action_label, guard, destinations):
        self.source_loc = source_loc
        self.action_label = action_label
        self.guard = guard
        self.destinations = destinations

    def _destinations_to_prism_string(self):
        complete_updates = []
        for update, loc in self.destinations:
            asgs = update.assignments
            for var, val in loc.val_map.items():
                asgs.append(sp.PrismAssignment(var, val))
            complete_updates.append(sp.PrismUpdate(update.global_index, update.probability_expression, asgs))
        return " + ".join(str(update) for update in complete_updates)

    def to_prism_string(self):
        guard_strings = [str(self.guard)]
        if not self.source_loc.is_empty:
            guard_strings.append(self.source_loc.to_prism_string())
        guard_string = " & ".join(reversed(guard_strings))
        return "[{}] {} -> {};\n".format(
            self.action_label,
            guard_string,
            self._destinations_to_prism_string()
        )


class PCFPModule:
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

    _orig_prism_module: sp.PrismModule
    _parent_composition: PCFPComposition

    _graph: nx.MultiDiGraph

    # unique initial location, derived from initial values
    _initial_loc: Location

    # getters/setters

    @property
    def commands(self):
        return self._commands

    # constructors

    def __init__(self):
        self._commands = []
        self.int_variables_bounds = {}
        self.boolean_variables = []
        self.initial_values = {}
        self.initial_locs = set()
        self._undef_constants = []
        self._undef_constants_types = dict()
        self._orig_prism_module = None
        self._parent_composition = None
        self._graph = nx.MultiDiGraph()
        self._initial_loc = None

    def copy(self):
        new_pcfp = PCFPModule()
        new_pcfp._commands = list.copy(self._commands)
        new_pcfp.int_variables_bounds = dict.copy(self.int_variables_bounds)
        new_pcfp.initial_values = dict.copy(self.initial_values)
        new_pcfp.initial_locs = set.copy(self.initial_locs)
        new_pcfp._undef_constants = list.copy(self._undef_constants)
        new_pcfp._undef_constants_types = dict.copy(self._undef_constants_types)
        return new_pcfp

    def add_update(self, cmd_node: CmdNode, target_loc: Location, update: sp.PrismUpdate):
        # TODO check here if update is already there
        # this creates a new edge with the prism_update as data
        self._graph.add_edge(cmd_node, target_loc, update=update)

    @classmethod
    def from_prism_module(cls, prism_module: sp.PrismModule):
        instance = PCFPModule()
        instance._orig_prism_module = prism_module

        # local int variables of this module
        for int_var in prism_module.integer_variables:
            # lower/upper bound
            lower_upper = (int_var.lower_bound_expression, int_var.upper_bound_expression)
            instance.int_variables_bounds[int_var.expression_variable] = lower_upper
            # initial value
            instance.initial_values[int_var.expression_variable] = int_var.initial_value_expression

        # local bool variables of this module
        for bool_var in prism_module.boolean_variables:
            # no bounds for bool vars
            bool_var: sp.PrismBooleanVariable
            instance.boolean_variables.append(bool_var.expression_variable)
            # initial value
            instance.initial_values[bool_var.expression_variable] = bool_var.initial_value_expression

        # commands
        single_loc = Location()  # create single location without any valuation
        instance._initial_loc = single_loc
        instance._graph.add_node(single_loc)
        for prism_cmd in prism_module.commands:
            # create a node belonging to the command (stores label/guard) and connect with loc
            cmd_node = CmdNode(prism_cmd.action_name, prism_cmd.guard_expression)
            instance._graph.add_edge(single_loc, cmd_node)

            for prism_update in prism_cmd.updates:
                instance.add_update(cmd_node, single_loc, update=prism_update)

        return instance

    @property
    def name(self) -> str:
        return self._orig_prism_module.name

    @property
    def expression_manager(self) -> sp.ExpressionManager:
        return self._parent_composition.expression_manager

    def set_parent_composition(self, pcfp_composition: PCFPComposition):
        self._parent_composition = pcfp_composition

    @property
    def local_variables(self):
        """Iterates of the local variables of this module"""
        for int_var in self.int_variables_bounds.keys():
            yield int_var
        for bool_var in self.boolean_variables:
            yield bool_var

    def has_local_variable(self, var: sp.Variable) -> bool:
        return var in self.local_variables

    @property
    def locations(self) -> Generator[Location]:
        """Iterate over locations"""
        return (node for node in self._graph.nodes if isinstance(node, Location))

    def get_commands(self) -> Generator[Command]:
        for node in self._graph.nodes:
            if isinstance(node, CmdNode):
                source_loc = next(self._graph.predecessors(node))
                destinations = []
                for _, target_loc, update in self._graph.out_edges(node, data='update'):
                    destinations.append((update, target_loc))
                yield Command(source_loc, node.action_label, node.guard, destinations)

    @property
    def nr_locations(self) -> int:
        return sum(1 for _ in self.locations)

    def get_values_for_local_var(self, var: sp.Variable) -> Generator[sp.Expression]:
        """Generator over possible values for the given local variable"""
        exp_mgr: sp.ExpressionManager = self.expression_manager
        if var.has_integer_type():
            bounds = self.int_variables_bounds[var]  # tuple of lower/upper bound
            # check if variable bounds depend on undefined constants
            if bounds[0].contains_variables() or bounds[1].contains_variables():
                raise Exception("bounds of variable {} have undef constants".format(var.name))
            lower_bound: int = bounds[0].evaluate_as_int()
            upper_bound: int = bounds[1].evaluate_as_int()
            # both bounds are inclusive
            return (exp_mgr.create_integer(val) for val in range(lower_bound, upper_bound + 1))
        elif var.has_boolean_type():
            return (exp_mgr.create_boolean(val) for val in [True, False])
        else:
            raise Exception("only int or boolean variables are supported")

    def remove_unreachable_locs(self):
        nr_locs_before = self.nr_locations
        new_graph = nx.MultiDiGraph()
        for u, v, key in nx.edge_bfs(self._graph, source=self._initial_loc, orientation=None):
            if 'update' in self._graph[u][v][key]:
                new_graph.add_edge(u, v, update=self._graph[u][v][key]['update'])
            else:
                new_graph.add_edge(u, v)
        self._graph = new_graph
        nr_locs_after = self.nr_locations
        logging.info("{} unreachable locations were removed".format(nr_locs_before - nr_locs_after))

    def unfold(self, var: sp.Variable):
        """Unfolds the given variable into the location space"""
        if not self.has_local_variable(var):
            raise Exception("Variable {} is no local variable in module {}".format(var.name, self.name))
        # TODO check unfoldable (is done further below)?
        # if not self.is_unfoldable(var):
        #    raise Exception("The variable cannot be unfolded")

        # the returns u[v] and u(v)(x) in paper notation
        def substitute_and_remove_const_lhs(udpate: sp.PrismUpdate, substitution) -> (sp.PrismUpdate, object):
            update_subst = update.substitute(substitution).simplify()
            # the value u(v)(x)
            if var in update_subst.get_as_variable_to_expression_map():
                new_target_loc_val = update_subst.get_assignment(var.name).expression
            else:
                new_target_loc_val = substitution[var]
            new_asgs = []
            # only keep assignments whose lhs variable is not substituted
            for asg in update_subst.assignments:
                if asg.variable in substitution:
                    continue
                new_asgs.append(asg)
            new_update = sp.PrismUpdate(update.global_index, update.probability_expression, new_asgs)
            return new_update, new_target_loc_val

        new_graph = nx.MultiDiGraph()

        for val in self.get_values_for_local_var(var):
            # substitution to be plugged into all locs/cmds for this particular value of var
            substitution = {var: val}
            for loc in self.locations:
                logging.debug("substituting {} in location {}".format(substitution, loc))
                new_loc = loc.extend(substitution)
                if new_loc.is_initial(self.initial_values):
                    logging.debug("initial location was set to {}".format(new_loc))
                    self._initial_loc = new_loc
                for cmd_node in self._graph.successors(loc):
                    new_guard = cmd_node.guard.substitute(substitution).simplify()
                    # if the guard has evaluated to false then ignore the whole command
                    if not new_guard.contains_variables() and new_guard.evaluate_as_bool() is False:
                        continue
                    # otherwise create the new node and add to graph
                    new_cmd_node = CmdNode(cmd_node.action_label, new_guard)
                    new_graph.add_edge(new_loc, new_cmd_node)
                    # process each update of the command
                    for _, target_loc, update in self._graph.out_edges(cmd_node, data="update"):
                        # this also substitutes the probability expression in the update
                        new_update, new_target_loc_val = substitute_and_remove_const_lhs(update, substitution)
                        new_target_loc = target_loc.extend({var: new_target_loc_val})
                        if new_target_loc_val.contains_variables():
                            logging.error(f"variable {var.name} was not unfoldable")
                        new_graph.add_edge(new_cmd_node, new_target_loc, update=new_update)

        self._graph = new_graph
        self.remove_unreachable_locs()
        logging.info("finished unfolding, there are now {} locations in {}".format(self.nr_locations, self.name))

    # converts this PCFP to a PRISM program as string
    def to_prism_string(self) -> str:
        res = ""

        res += "module {}\n".format(self.name)

        for var in self.int_variables_bounds:
            res += "\t{}: [{}..{}] init {};\n" \
                .format(var.name, self.get_lower_bound(var), self.get_upper_bound(var), self.initial_values[var])

        for var in self.boolean_variables:
            res += "\t{}: bool init {};\n".format(var.name, self.initial_values[var])

        for cmd in self.get_commands():
            res += "\t" + cmd.to_prism_string()

        res += "endmodule\n"
        return res

    # public functions

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

    def _local_int_var_bounds_constraints(self) -> Generator[sp.Expression]:
        for var, (lower, upper) in self.int_variables_bounds.items():
            yield sp.Expression.Geq(var.get_expression(), lower)
            yield sp.Expression.Leq(var.get_expression(), upper)

    def _is_surely_unsat(self, exp: sp.Expression) -> bool:
        # use SMT solver to check expression with this module's variable bounds
        solver = Z3SmtSolver(self.expression_manager)
        solver.add(exp)
        for constraint in self._local_int_var_bounds_constraints():
            solver.add(constraint)
        for constant in self._parent_composition.undef_constants:
            if constant.type.is_integer:
                # constants must be non-negative
                solver.add(
                    sp.Expression.Geq(
                        self.expression_manager.get_variable(constant.name).get_expression(),
                        self.expression_manager.create_integer(0)
                    )
                )
        solver.push()
        if solver.check() == SmtCheckResult.Unsat:
            return True
        else:
            return False

    def eliminate_transition(self, cmd_node: CmdNode, target_loc: Location, key: int):

        def wp(update: sp.PrismUpdate, post_cond: sp.Expression) -> sp.Expression:
            return post_cond.substitute(update.get_as_variable_to_expression_map()).simplify()

        # sequences two updates
        def seq(update_left, update_right):
            map_right_subst = update_right.substitute(update_left.get_as_variable_to_expression_map()).get_as_variable_to_expression_map()
            map_left = update_left.get_as_variable_to_expression_map()
            for key, val in map_right_subst.items():
                map_left[key] = val  # overwrite
            new_asgs = []
            for key, val in map_left.items():
                new_asgs.append(sp.PrismAssignment(key, val))
            new_probability = sp.Expression.Multiply(update_left.probability_expression, update_right.probability_expression).simplify()
            new_update = sp.PrismUpdate(update_right.global_index, new_probability, new_asgs)
            return new_update

        update = self._graph[cmd_node][target_loc][key]['update']
        label = cmd_node.action_label
        guard = cmd_node.guard
        prob = update.probability_expression
        source_loc = next(self._graph.predecessors(cmd_node))

        succs = frozenset(self._graph.successors(target_loc))
        for next_cmd_node in succs:
            next_guard = next_cmd_node.guard
            next_label = next_cmd_node.action_label
            new_label = "_".join(lab for lab in [label, next_label] if lab != '')
            new_guard = sp.Expression.And(guard, wp(update, next_guard)).simplify()

            # ignore if new guard is guaranteed to be unsat
            if self._is_surely_unsat(new_guard):
                logging.debug(f"new guard us unsat: '{new_guard}'")
                continue

            new_cmd_node = CmdNode(new_label, new_guard)
            self._graph.add_edge(source_loc, new_cmd_node)

            for _, other_target_loc, other_key, other_update in self._graph.out_edges(cmd_node, data='update', keys=True):
                self._graph.add_edge(new_cmd_node, other_target_loc, update=other_update, key=other_key)

            self._graph.remove_edge(new_cmd_node, target_loc, key)


            for _, next_target_loc, next_update in self._graph.out_edges(next_cmd_node, data='update'):
                new_update = seq(update, next_update)
                self._graph.add_edge(new_cmd_node, next_target_loc, update=new_update)

        # finally eliminate node cmd_node from the graph
        self._graph.remove_node(cmd_node)

    # if loc has no self-loops then it will be unreachable after applying this function
    def eliminate_loc(self, loc: Location):
        logging.info("eliminating {}...".format(loc))
        t_start = time.time()

        # not sure why I had to use iter here ...
        to_eliminate = next(iter(self._graph.in_edges(loc, keys=True)), None)  # tuples u,v,k or None
        while to_eliminate:
            cmd_node = to_eliminate[0]
            # loc = to_eliminate[1], same as input loc
            key = to_eliminate[2]
            #logging.debug("eliminate transition {} ---{}---> {}".format(cmd.source_loc, cmd.guard, dest))
            self.eliminate_transition(cmd_node, loc, key)
            to_eliminate = next(iter(self._graph.in_edges(loc, keys=True)), None)

        self.remove_unreachable_locs()
        t_end = time.time()
        logging.info("...elimination took {}s".format(t_end - t_start))

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

    def has_loc_selfloop(self, loc: Location):
        for cmd_node in self._graph.successors(loc):
            if loc in self._graph.successors(cmd_node):
                return True
        return False

    def eliminable_locs(self, goal_predicate: sp.Expression) -> Generator[Location]:
        """Iterate over all locations that have no self loops, are not initial nor potential goals."""
        for loc in self.locations:
            if loc is not self._initial_loc and not loc.is_potential_goal(goal_predicate):
                if not self.has_loc_selfloop(loc):
                    yield loc

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
