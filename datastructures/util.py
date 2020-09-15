
# compare locations given as {sp.Variable: sp.Expression}
# currently only works for int variables
def are_locs_equal(loc1, loc2) -> bool:
    if len(loc1) != len(loc2):
        return False
    return all([loc1[v].evaluate_as_int() == loc2[v].evaluate_as_int() for v in loc1])