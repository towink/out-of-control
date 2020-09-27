import stormpy
from typing import Dict
from locelim.datastructures.PCFP import PCFP

from locelim.datastructures.command import Command


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


def unfold(old_model: PCFP, base_jani_model: stormpy.JaniModel, elimination_names: [str]) -> PCFP:
    """

    :rtype: object
    """
    # Based on this: https://github.com/moves-rwth/storm/blob/master/src/storm/storage/jani/JaniLocationExpander.cpp
    # but with support for unfolding multiple variables at the same time

    new_model: PCFP = PCFP(base_jani_model)

    # Remove variables from model and father information on the values each one can assume:
    elimination_info = eliminate_variables(elimination_names, base_jani_model.expression_manager, old_model, new_model)
    # Generate all possible combinations of values the eliminated variables can assume:
    variable_combinations = build_variable_combinations(elimination_info)
    variable_combination_names: [str] = []
    for var_comb in variable_combinations:
        name = ""
        for var, val in var_comb.items():
            name += var.name + "=" + str(val) + ";"
        variable_combination_names.append(name)

    def get_new_location(old_location: object, variable_combination: Dict[stormpy.Variable, stormpy.Expression]):
        if len(variable_combination) != len(elimination_info):
            raise Exception("To get the new location, all variable assignments have to be specified")
        for (i, candidate) in enumerate(variable_combinations):
            match = True
            for var in candidate:
                cand_value = candidate[var].evaluate_as_int()
                comb_value = variable_combination[var].evaluate_as_int()
                if cand_value != comb_value:
                    match = False
                    break
            if match:
                return old_location, variable_combination_names[i]
        raise Exception("The variables are out of bound")

    # Set the initial locations:

    initial_variable_combination = {}
    for variable_info in elimination_info:
        initial_variable_combination[variable_info.variable] = variable_info.init_expression
    for old_initial_loc in old_model.initial_locs:
        new_initial_loc = get_new_location(old_initial_loc, initial_variable_combination)
        new_model.initial_locs.add(new_initial_loc)

    for command in old_model.commands:
        for (i, variable_combination) in enumerate(variable_combinations):
            new_source_loc = get_new_location(command.source_loc, variable_combination)

            new_guard = command.guard.substitute(variable_combination).simplify()

            # Skip commands where the guard evaluates to false
            if not new_guard.contains_variables() and not new_guard.evaluate_as_bool():
                continue

            new_destinations: [Command.Destination] = []
            for old_destination in command.destinations:
                old_destination: Command.Destination

                new_prob = old_destination.probability.substitute(variable_combination).simplify()
                # TODO: Skip destination if probability is zero

                new_values = old_destination.update.apply(variable_combination)
                new_target_loc = get_new_location(old_destination.target_loc, new_values)

                new_update = old_destination.update.remove_variables(variable_combination)

                new_destination = Command.Destination(new_prob, new_update, new_target_loc)
                new_destinations.append(new_destination)

            new_command: Command = Command(new_source_loc, new_guard, new_destinations)
            new_model.add_command(new_command)

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


def eliminate_variables(elimination_names: [str], expression_manager: stormpy.ExpressionManager, model: PCFP, new_model: PCFP):
    elimination_info: [VariableInfo] = []
    var: stormpy.JaniBoundedIntegerVariable
    for var in model.int_variables_bounds:

        lower_bound, upper_bound = model.int_variables_bounds[var]
        lower_bound: stormpy.Expression
        upper_bound: stormpy.Expression

        init_expression = model.initial_values[var]

        if var.name in elimination_names:
            if lower_bound.contains_variables() or upper_bound.contains_variables():
                raise Exception("Cannot unfold because the bounds aren't a constant")
            if init_expression.contains_variables():
                # This might not actually be a problem?
                raise Exception("Cannot unfold because the initial value isn't a constant")

            lower_bound_value, upper_bound_value = lower_bound.evaluate_as_int(), upper_bound.evaluate_as_int()

            values = [expression_manager.create_integer(val) for val in range(lower_bound_value, upper_bound_value)]
            elimination_info.append(VariableInfo(var, init_expression, values))

        else:
            new_model.int_variables_bounds[var] = (lower_bound, upper_bound)
            new_model.initial_values[var] = init_expression

    return elimination_info
