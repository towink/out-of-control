from ooc.benchmarks.benchmark_utils import stat_vars
from ooc.interactive import *
from ooc.models.files import leader_sync_4_8_prism


def leader_sync():
    reset_session()

    load_model(leader_sync_4_8_prism)
    # P>=1 [ F "elected" ]
    # set_property("P=? [ F s1=3&s2=3&s3=3 ]")  # for 3-x
    set_property("P=? [ F s1=3&s2=3&s3=3&s4=3 ]")  # for 4-x
    # set_property("P=? [ F s1=3&s2=3&s3=3&s4=3&s5=3 ]")  # for 5-x
    # set_property("P=? [ F s1=3&s2=3&s3=3&s4=3&s5=3&s6=3 ]")  # for 6-x


    model_orig, time_build_orig = session().build_orig_model(return_time=True)
    res_orig, time_check_orig = session().check_orig_model(return_time=True)
    states_orig = model_orig.nr_states
    transitions_orig = model_orig.nr_transitions

    pcfp_stats = session().get_pcfp_stats()
    orig_locs = pcfp_stats["locations"]
    orig_cmds = pcfp_stats["commands"]
    orig_trans = pcfp_stats["transitions"]

    t_start = time.time()

    # start of simplification
    flatten()
    unfold("s1")
    eliminate_all()
    unfold("c")
    eliminate({"s1": 1, "c": 2})
    # end of simplification

    t_end = time.time()
    time_simplification = t_end - t_start

    model_simpl, time_build_simpl = session().build_model(return_time=True)
    res_simpl, time_check_simpl = session().check_model(return_time=True)
    states_simpl = model_simpl.nr_states
    transitions_simpl = model_simpl.nr_transitions

    pcfp_stats = session().get_pcfp_stats()
    simpl_locs = pcfp_stats["locations"]
    simpl_cmds = pcfp_stats["commands"]
    simpl_trans = pcfp_stats["transitions"]

    local_vars = locals()
    benchmark_info = dict([(var, local_vars[var]) for var in stat_vars])
    benchmark_info['name'] = 'leader\\_sync'
    benchmark_info['constant_defs'] = {"N": 8, "K": 4}

    for key, value in benchmark_info.items():
        print("{}: {}".format(key, value))

    return benchmark_info


if __name__ == "__main__":
    # uncomment to disable logging
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
    leader_sync()
