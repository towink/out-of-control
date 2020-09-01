import stormpy
from typing import Dict
import pycarl.gmp


class VariableInfo:
    variable: stormpy.Variable = None
    init_expression: stormpy.Expression
    values: [stormpy.Expression] = []

    def __init__(self, variable: stormpy.Variable, init_expression: stormpy.Expression, values: [stormpy.Expression]):
        self.variable = variable
        self.init_expression = init_expression
        self.values = values


def build_variable_combinations(variables: [VariableInfo]) -> [Dict[stormpy.Variable, stormpy.Expression]]:  # The type of the values in the return dict probably shouldn't be a string either
    combinations: [Dict[stormpy.Variable, stormpy.Expression]] = [{}]

    for var in variables:
        new_combinations: [Dict[stormpy.Variable, stormpy.Expression]] = []
        for old_combination in combinations:
            for val in var.values:
                new_combination = dict(old_combination)
                new_combination[var.variable] = val
                new_combinations.append(new_combination)
        combinations = new_combinations

    return combinations


def get_index_in_dictionary_list(list: [Dict], search: Dict) -> int:
    entry: Dict
    for i, entry in enumerate(list):
        if len(entry.keys()) != len(search.keys()):
            continue
        same: bool = True
        for key in entry.keys():
            entry_expr: stormpy.Expression = entry[key]
            search_expr: stormpy.Expression = search[key]
            # This might be a bit inefficient:
            equal_expr: stormpy.Expression = entry_expr.Eq(entry_expr, search_expr)
            if not equal_expr.evaluate_as_bool():
                same = False

        if same:
            return i

    return -1


def unfold(old_model: stormpy.JaniModel, elimination_names: [str]) -> stormpy.JaniModel:
    # Based on this: https://github.com/moves-rwth/storm/blob/master/src/storm/storage/jani/JaniLocationExpander.cpp
    # but with support for unfolding multiple variables at the same time



    if len(old_model.automata) != 1:
        raise Exception("Can only unfold models that have exactly one automaton. Please flatten the model first")
    old_automaton: stormpy.JaniAutomaton = old_model.automata[0]

    new_model: stormpy.JaniModel = stormpy.JaniModel(old_model)
    new_automaton: stormpy.JaniAutomaton = stormpy.JaniAutomaton(old_automaton.name, old_automaton.location_variable)

    # Remove variables from model and father information on the values each one can assume:
    elimination_info = eliminate_variables(elimination_names, old_model.expression_manager, old_model, new_model)
    # Generate all possible combinations of values the eliminated variables can assume:
    variable_combinations = build_variable_combinations(elimination_info)

    # Each location will turn into len(variable_combinations) new locations. The indices of these new locations are
    # stored in this list. Each list entry corresponds to a value combination and is a dictionary that maps old location
    # indices to new location indices
    new_location_indices: [Dict[int, int]] = [dict() for _ in variable_combinations]

    loc: stormpy.JaniLocation
    for loc in old_automaton.locations:
        if loc.assignments is not None:
            raise Exception("Location assignments are not supported")

        for i, variable_combination in enumerate(variable_combinations):
            loc_name: str = loc.name
            key: stormpy.Variable
            value: stormpy.Expression
            for key, value in variable_combination.items():
                loc_name += "; " + str(key.name) + "=" + str(value)

            new_loc = stormpy.JaniLocation(loc_name, stormpy.JaniOrderedAssignments([]))

            index = new_automaton.add_location(new_loc)
            old_index = old_automaton.get_location_index(loc.name)
            new_location_indices[i][old_index] = index

            if old_index in old_automaton.initial_location_indices:
                if is_variable_combination_initial(elimination_info, variable_combination):
                    new_automaton.add_initial_location(index)

    old_edge: stormpy.JaniEdge
    for old_edge in old_automaton.edges:
        for i, variable_combination in enumerate(variable_combinations):
            guard: stormpy.Expression = old_edge.guard.substitute(variable_combination).simplify()

            # Skip edges where the guard evaluates to false
            if not guard.contains_variables() and not guard.evaluate_as_bool():
                continue

            template_edge: stormpy.JaniTemplateEdge = stormpy.JaniTemplateEdge(guard)
            destination_indices_and_probabilities: [(int, stormpy.Expression)] = []

            out_of_bounds: bool = False  # Tracks whether a destination is out of bounds.

            destination: stormpy.JaniEdgeDestination
            for destination in old_edge.destinations:
                assignments: stormpy.JaniOrderedAssignments = destination.assignments.clone()
                assignments.substitute(variable_combination)

                new_assignments = stormpy.JaniOrderedAssignments([])

                new_variable_values = dict(variable_combination)

                assignment: stormpy.JaniAssignment
                for assignment in assignments:
                    variable: stormpy.JaniVariable = assignment.variable
                    if variable.name in elimination_names:
                        expression: stormpy.Expression = assignment.expression
                        if expression.contains_variables():
                            raise Exception("Cannot unfold variable " + variable.name + ".")
                        new_variable_values[variable.expression_variable] = expression
                    else:
                        new_assignments.add(assignment)

                template_edge_destination: stormpy.JaniTemplateEdgeDestination = stormpy.JaniTemplateEdgeDestination(new_assignments)
                template_edge.add_destination(template_edge_destination)

                destination_index: int = get_index_in_dictionary_list(variable_combinations, new_variable_values)
                if destination_index == -1:
                    print("WARNING: A variable bound was violated and the edge omitted from the model")
                    out_of_bounds = True
                    break

                probability_expression: stormpy.Expression = destination.probability
                probability_expression = probability_expression.substitute(variable_combination).simplify()
                destination_indices_and_probabilities.append((destination_index, probability_expression))

            if out_of_bounds:  # Don't add edges where a destination was out of bounds
                continue

            edge_start_index = new_location_indices[i][old_edge.source_location_index]
            new_edge: stormpy.JaniEdge = stormpy.JaniEdge(edge_start_index, old_edge.action_index, old_edge.rate, template_edge, destination_indices_and_probabilities)
            new_automaton.add_edge(new_edge)

    # As new_model is a copy of the existing model, we need to replace the automaton with the new one:
    new_model.replace_automaton(0, new_automaton)
    return new_model


def is_variable_combination_initial(elimination_info, value_combination):
    is_initial: bool = True
    eliminated_var: VariableInfo
    for eliminated_var in elimination_info:
        value = value_combination[eliminated_var.variable]
        init_value = eliminated_var.init_expression
        equal: stormpy.Expression = value.Eq(value, init_value)
        if not equal.evaluate_as_bool():
            is_initial = False
    return is_initial


def eliminate_variables(elimination_names, expression_manager, model, new_model):
    elimination_info: [VariableInfo] = []
    var: stormpy.JaniBoundedIntegerVariable
    for var in model.global_variables:
        # This crashes if var is not a bounded integer variable. TODO: Add a check for this
        # Adding support for bools should not be difficult
        lower_bound: int = var.lower_bound.evaluate_as_int()
        upper_bound: int = var.upper_bound.evaluate_as_int()
        init_expression: stormpy.Expression = var.init_expression
        init_expression_value: int = init_expression.evaluate_as_int()

        print("Variable " + var.name + ": Range [" + str(lower_bound) + "," + str(upper_bound) + "], Init Value " + str(
            init_expression_value))

        if var.name in elimination_names:
            print("The variable will be unfolded")
            values = [expression_manager.create_integer(val) for val in range(lower_bound, upper_bound)]
            elimination_info.append(VariableInfo(var.expression_variable, init_expression, values))
            new_model.global_variables.erase_variable(var.expression_variable)
        else:
            print("The variable will not be unfolded")

        print("")
    return elimination_info



