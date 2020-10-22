import stormpy as sp


def exp_to_primitive_type(exp: sp.Expression):
    # converts an int/bool as an expression to a builtin int or bool
    if exp.has_boolean_type():
        return exp.evaluate_as_bool()
    elif exp.has_integer_type():
        return exp.evaluate_as_int()
    else:
        raise Exception("unsupported type")


def primitive_type_to_exp(value: object, mgr: sp.ExpressionManager) -> sp.Expression:
    # converts builtin type to expression
    if type(value) == int:
        return mgr.create_integer(value)
    elif type(value) == bool:
        return mgr.create_boolean(value)
    else:
        raise Exception("unsupported type")


def are_locs_equal(loc1, loc2) -> bool:
    # compare locations given as {sp.Variable: sp.Expression}
    if len(loc1) != len(loc2):
        return False
    return all([exp_to_primitive_type(loc1[v]) == exp_to_primitive_type(loc2[v]) for v in loc1])
