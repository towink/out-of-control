import stormpy as sp

# converts an int/bool as an expression to a builtin int or bool
def exp_to_primitive_type(exp: sp.Expression):
    if exp.has_boolean_type():
        return exp.evaluate_as_bool()
    elif exp.has_integer_type():
        return exp.evaluate_as_int()
    else:
        raise Exception

# compare locations given as {sp.Variable: sp.Expression}
# currently only works for int variables
def are_locs_equal(loc1, loc2) -> bool:
    if len(loc1) != len(loc2):
        return False
    return all([exp_to_primitive_type(loc1[v]) == exp_to_primitive_type(loc2[v]) for v in loc1])