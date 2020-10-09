
def count_transitions(model):
    raise Exception("don't use me")


stat_vars = ['states_orig', 'transitions_orig',
                 'states_simpl', 'transitions_simpl',
                 'time_build_orig', 'time_build_simpl',
                 'time_check_orig', 'time_check_simpl',
                 'time_simplification',
                 'orig_locs', 'orig_cmds', 'orig_trans',
                 'simpl_locs', 'simpl_cmds', 'simpl_trans']

def NA_latex_string(name):
    na = "\\texttt{NA}"
    return f"\\textsc{{{name}}} & {na} &{na} &{na} &{na} &{na} &{na} &{na} &{na} &{na} &{na} &{na} &{na} \\\\ \n"

def to_latex_string(benchmark_info):

    def format_constant_defs(constant_defs):
        return ",".join([str(val) for val in constant_defs.values()])

    return "\\textsc{{{}}} & {} & {:,.0f} & {:,.0f} & {:,.0f} & {:,.0f} & {:.2f} & {:.2f} & {:.2f} & {:.2f} & {:.2f} & {} & {} \\\\ \n".format(
        benchmark_info['name'],
        format_constant_defs(benchmark_info['constant_defs']),

        benchmark_info['states_orig'] / 1000,
        benchmark_info['states_simpl'] / 1000,
        benchmark_info['transitions_orig'] / 1000,
        benchmark_info['transitions_simpl'] / 1000,

        benchmark_info['time_build_orig'],
        benchmark_info['time_build_simpl'],
        benchmark_info['time_check_orig'],
        benchmark_info['time_check_simpl'],

        benchmark_info['time_simplification'],

        #benchmark_info['orig_locs'],
        #benchmark_info['orig_cmds'],
        benchmark_info['orig_trans'],

        #benchmark_info['simpl_locs'],
        #benchmark_info['simpl_cmds'],
        benchmark_info['simpl_trans'],
    )




