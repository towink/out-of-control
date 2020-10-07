from locelim.interactive import *
from locelim.benchmarks.benchmark_utils import count_transitions, to_latex_string


def handcrafted():
    # comment out to disable logging
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)

    load_model("originals/coupon.prism")
    constant_defs = {"N": 10000}
    def_model_constants(constant_defs)
    set_property("P=? [ F c0 & c1 & c2 & c3 & s=2 & c=N]")

    model_orig, time_build_orig = session().build_orig_model(return_time=True)
    res_orig, time_check_orig = session().check_orig_model(return_time=True)
    states_orig = len(model_orig.states)
    transitions_orig = count_transitions(model_orig)

    t_start = time.time()

    # actual simplification starts here
    show_as_prism()
    session().unfold("s")

    eliminate({"s": 1})
    #eliminate_all()
    show_eliminable_locations()
    show_loc_info()
    show_eliminable_locations()
    unfold("draw")
    eliminate_all()
    show_eliminable_locations()
    show_loc_info()
    unfold("c0")
    show_eliminable_locations()
    eliminate_all()

    #eliminate({"s": 2})
    #eliminate_all()

    t_end = time.time()
    time_simplification = t_end - t_start

    model_simpl, time_build_simpl = session().build_model(return_time=True)
    res_simpl, time_check_simpl = session().check_model(return_time=True)
    states_simpl = len(model_simpl.states)
    transitions_simpl = count_transitions(model_simpl)

    print("result orig: {}".format(res_orig))
    print("result simpl: {}".format(res_simpl))

    stat_vars = ['states_orig', 'transitions_orig',
                 'states_simpl', 'transitions_simpl',
                 'time_build_orig', 'time_build_simpl',
                 'time_check_orig', 'time_check_simpl',
                 'time_simplification']
    local_vars = locals()
    benchmark_info = dict([(var, local_vars[var]) for var in stat_vars])
    benchmark_info['name'] = 'handcrafted'
    benchmark_info['constant_defs'] = constant_defs
    for key, value in benchmark_info.items():
        print("{}: {}".format(key, value))

    return benchmark_info


if __name__ == "__main__":
    benchmark_info = handcrafted()
    print(to_latex_string(benchmark_info))
