from typing import Dict
import logging

import stormpy as sp

from datastructures.command import Command
from datastructures.update import AtomicUpdate, Assignment


# a probabilistic control flow program (a restricted form of jani program)
class PCFP:
    _commands: [Command] = []

    # lower/upper bound for bounded integer variables only
    _variable_bounds: Dict[sp.Variable, sp.Expression] = {}

    # unique initial variable valuation for all variables
    _initial_values: Dict[sp.Variable, sp.Expression] = {}

    # initial locations
    _initial_locs: {object} = set()

    # all undefined constants, may appear in variable bounds, guards, probabilities, updates
    # TODO probably better to refer to orig jani for this
    _undef_constants: [sp.Variable] = []

    # jani model this PCFP was originally constructed from, is used to export to jani again
    _original_jani: sp.JaniModel = None

    def add_command(self, cmd: Command):
        self._commands.append(cmd)

    def locations(self) -> {object}:
        s = {cmd.source_loc for cmd in self._commands}
        return s

    # construct a PCFP object from a jani model
    @classmethod
    def from_jani(cls, jani_model: sp.JaniModel):
        if not jani_model.check_valid():
            logging.warning("provided jani_model is not valid")
        if len(jani_model.automata) > 1:
            logging.warning("jani models with multiple automata are not supported, ignoring all but first")
        automaton: sp.JaniAutomaton = jani_model.automata[0]
        new_instance = PCFP()
        new_instance._original_jani = jani_model

        # variable bounds
        for jani_var in jani_model.global_variables:
            jani_var: sp.JaniVariable
            if type(jani_var) is not sp.JaniBoundedIntegerVariable:
                continue
            var = jani_var.expression_variable
            lower_bound = jani_var.lower_bound
            upper_bound = jani_var.upper_bound
            new_instance._variable_bounds[var] = (lower_bound, upper_bound)

        # undefined constants
        for constant in jani_model.constants:
            new_instance._undef_constants.append(constant.expression_variable)

        # commands
        for edge in automaton.edges:
            edge: sp.JaniEdge
            source_loc = automaton.locations[edge.source_location_index]
            guard = edge.guard
            destinations = []
            for dest in edge.destinations:
                target_loc = automaton.locations[dest.target_location_index]
                probability = dest.probability
                update = AtomicUpdate()
                for asg in dest.assignments:
                    update.add_assignment(Assignment(asg.variable, asg.expression))
                destinations.append(Command.Destination(probability, update, target_loc))
            cmd = Command(source_loc, guard, destinations)
            new_instance.add_command(cmd)

        # initial locations
        for index in automaton.initial_location_indices:
            new_instance._initial_locs.add(automaton.locations[index])

        return new_instance

    # builds a JaniModel from this PCFP instance
    def to_jani(self) -> sp.JaniModel:
        # construct resulting jani model using the original jani model
        if self._original_jani is None:
            raise Exception("can only export to jani if PCFP was constructed with from_jani(...)")
        jani_model: sp.JaniModel = self._original_jani
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
        for initial_loc in self._initial_locs:
            initial_loc_index = location_list.index(initial_loc)
            automaton.add_initial_location(initial_loc_index)

        # commands/edges
        for cmd in self._commands:
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
                for asg in dest.update._par_assignments:
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
