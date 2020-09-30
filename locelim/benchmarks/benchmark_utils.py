def count_transitions(model):
    # counts transitions in a built model
    # TODO is quite slow
    res = 0
    for s in model.states:
        for act in s.actions:
            res += len(act.transitions)
    return res


stat_vars = ['name', 'constant_defs',
             'states_orig', 'transitions_orig',
             'states_simpl', 'transitions_simpl',
             'time_build_orig', 'time_build_simpl',
             'time_check_orig', 'time_check_simpl',
             'time_simplification']


def to_latex_string(benchmark_info):

    def format_constant_defs(constant_defs):
        # TODO join with comma
        res = ""
        for key, value in constant_defs.items():
            res += "{}={}".format(key, value)
        return res

    return "{} & {} & {:,} & {:,} & {:,} & {:,} & {:.3f} & {:.3f} & {:.3f} & {:.3f} & {:.3f}".format(
        benchmark_info['name'],
        format_constant_defs(benchmark_info['constant_defs']),

        benchmark_info['states_orig'],
        benchmark_info['states_simpl'],
        benchmark_info['transitions_orig'],
        benchmark_info['transitions_simpl'],

        benchmark_info['time_build_orig'],
        benchmark_info['time_build_simpl'],
        benchmark_info['time_check_orig'],
        benchmark_info['time_check_simpl'],

        benchmark_info['time_simplification'],
    )
