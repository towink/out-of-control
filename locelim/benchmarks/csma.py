from locelim.benchmarks.benchmark_utils import to_latex_string, stat_vars
from locelim.interactive import *


def csma():
    reset_session()

    # comment out to disable logging
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

    load_model("originals/csma.2-2.v1.prism")
    show_model_constants()
    set_property("Pmin=? [ F min_backoff_after_success<K ]")
    constant_defs = {} # "N": 10, "MAX": 20}
    def_model_constants(constant_defs)

    model_orig, time_build_orig = session().build_orig_model(return_time=True)
    res_orig, time_check_orig = session().check_orig_model(return_time=True)
    states_orig = len(model_orig.states)
    transitions_orig = model_orig.nr_transitions

    pcfp_stats = session().get_pcfp_stats()
    orig_locs = pcfp_stats["locations"]
    orig_cmds = pcfp_stats["commands"]
    orig_trans = pcfp_stats["transitions"]

    t_start = time.time()

    # actual simplification starts here
    session().unfold("s1")
    # session().unfold("s")
    # session().eliminate_all()
    # session().eliminate({"r":2 , "s": 6})  # this location is "lucky", it has self loop but can be eliminated
    # session().unfold("l")
    # session().unfold("k")
    # session().eliminate_all()
    # session().unfold("srep")
    # session().eliminate_all()
    # session().unfold("s_ab")
    # session().eliminate_all()

    t_end = time.time()
    time_simplification = t_end - t_start

    session().show_as_prism()

    model_simpl, time_build_simpl = session().build_model(return_time=True)
    res_simpl, time_check_simpl = session().check_model(return_time=True)
    states_simpl = len(model_simpl.states)
    transitions_simpl = model_simpl.nr_transitions

    print("result orig: {}".format(res_orig))
    print("result simpl: {}".format(res_simpl))

    # collect info for benchmark table

    pcfp_stats = session().get_pcfp_stats()
    simpl_locs = pcfp_stats["locations"]
    simpl_cmds = pcfp_stats["commands"]
    simpl_trans = pcfp_stats["transitions"]

    local_vars = locals()
    benchmark_info = dict([(var, local_vars[var]) for var in stat_vars])
    benchmark_info['name'] = 'brp'
    benchmark_info['constant_defs'] = constant_defs
    for key, value in benchmark_info.items():
        print("{}: {}".format(key, value))

    return benchmark_info


if __name__ == "__main__":
    benchmark_info = csma()
    print(to_latex_string(benchmark_info))
