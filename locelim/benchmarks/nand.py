from locelim.interactive import *
from locelim.benchmarks.benchmark_utils import count_transitions, to_latex_string


# manual analysis/benchmarking of nand

def nand():
    # comment out to disable logging
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

    load_model("originals/nand.prism")
    show_model_constants()
    set_property("P=? [ F s=4 & z/N<0.1 ]")
    constant_defs = {'N': 40, 'K': 4}
    def_model_constants(constant_defs)

    model_orig, time_build_orig = session().build_orig_model(return_time=True)
    res_orig, time_check_orig = session().check_orig_model(return_time=True)
    states_orig = len(model_orig.states)
    transitions_orig = count_transitions(model_orig)

    t_start = time.time()

    # actual simplification starts here
    session().unfold("s")
    session().eliminate({"s": 2})
    session().eliminate({"s": 3})
    session().eliminate({"s": 1})

    t_end = time.time()
    time_simplification = t_end - t_start

    model_simpl, time_build_simpl = session().build_model(return_time=True)
    res_simpl, time_check_simpl = session().check_model(return_time=True)
    states_simpl = len(model_simpl.states)
    transitions_simpl = count_transitions(model_simpl)

    stat_vars = ['states_orig', 'transitions_orig',
                 'states_simpl', 'transitions_simpl',
                 'time_build_orig', 'time_build_simpl',
                 'time_check_orig', 'time_check_simpl',
                 'time_simplification']
    local_vars = locals()
    benchmark_info = dict([(var, local_vars[var]) for var in stat_vars])
    benchmark_info['name'] = 'nand'
    benchmark_info['constant_defs'] = constant_defs
    for key, value in benchmark_info.items():
        print("{}: {}".format(key, value))

    return benchmark_info


if __name__ == "__main__":
    benchmark_info = nand()
    print(to_latex_string(benchmark_info))
