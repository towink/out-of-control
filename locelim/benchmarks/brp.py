from locelim.benchmarks.benchmark_utils import stat_vars
from locelim.interactive import *


def brp(constant_defs=None):
    reset_session()

    load_model("models/brp.prism")
    set_property("P=? [ F s=5 & srep=2 ]")
    if constant_defs is None:
        constant_defs = {"N": 2 ** 11, "MAX": 20}
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

    # start of simplification
    # unfolding r,s,l,k all at once makes a lot of locs unreachable!
    flatten()
    unfold("r")
    unfold("s")
    unfold("l")
    unfold("k")
    eliminate_all()
    unfold("srep")
    unfold("s_ab")
    eliminate_all()
    # end of simplification

    t_end = time.time()
    time_simplification = t_end - t_start

    model_simpl, time_build_simpl = session().build_model(return_time=True)
    res_simpl, time_check_simpl = session().check_model(return_time=True)
    states_simpl = len(model_simpl.states)
    transitions_simpl = model_simpl.nr_transitions

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
    # uncomment to disable logging
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
    brp()
