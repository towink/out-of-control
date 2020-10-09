
    # # unfolding start, recordLast, badObserve, deliver, done creates idempotent self loops
    # # unfolding new, start, recordLast, badObserve, deliver, creates eliminable locs
    #
    # show_pcfp_stats()
    # #unfold("launch")
    # unfold("new")
    # unfold("start")
    # #unfold("run")
    # #unfold("lastSeen")
    #
    # #unfold("good")
    # #unfold("bad")
    # unfold("recordLast")
    # unfold("badObserve")
    # unfold("deliver")
    # #unfold("done")
    # show_loc_info()
    # #show_as_prism()
    # #session().eliminate_unsatisfiable_commands()
    # #print(session()._pcfp.get_sink_locs_without_targets(session()._get_goal_predicate()))
    #
    # show_pcfp_stats()
    # #session()._pcfp.eliminate_nop_selfloops()
    # #show_eliminable_locations()
    # #eliminate_all()
    #
    # #eliminate({"new": False, "start": True, "recordLast": True, "badObserve": True, "deliver": True})
    # #eliminate({"new": False, "start": False, "recordLast": True, "badObserve": True, "deliver": True})
    # #eliminate({"new": False, "start": True, "recordLast": False, "badObserve": True, "deliver": True})
    # #eliminate({"new": False, "start": False, "recordLast": False, "badObserve": True, "deliver": True})
    # #eliminate({"new": False, "start": True, "recordLast": True, "badObserve": False, "deliver": True})
    # #eliminate({"new": False, "start": False, "recordLast": True, "badObserve": False, "deliver": True})
    # #eliminate({"new": False, "start": True, "recordLast": False, "badObserve": False, "deliver": True})
    # eliminate({"new": False, "start": False, "recordLast": False, "badObserve": False, "deliver": True})



from locelim.benchmarks.benchmark_utils import to_latex_string, stat_vars
from locelim.interactive import *


# manual analysis/benchmarking of crowds

def crowds(constant_defs=None):
    reset_session()

    # comment out to disable logging
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

    load_model("originals/crowds.prism")
    #set_property('P=? [ F observe0>1 & !launch & !new & !start & !run & lastSeen=0 & !good & !bad & done  & !recordLast & !badObserve & !deliver]')
    set_property('P=? [ F observe0>1  & !new & !start & !recordLast & !badObserve & !deliver]')
    if constant_defs is None:
        constant_defs = {'TotalRuns': 10, 'CrowdSize': 5}
    def_model_constants(constant_defs)

    model_orig, time_build_orig = session().build_orig_model(return_time=True)
    res_orig, time_check_orig = session().check_orig_model(return_time=True)
    states_orig = model_orig.nr_states
    transitions_orig = model_orig.nr_transitions

    pcfp_stats = session().get_pcfp_stats()
    orig_locs = pcfp_stats["locations"]
    orig_cmds = pcfp_stats["commands"]
    orig_trans = pcfp_stats["transitions"]

    t_start = time.time()

    # actual simplification starts here
    unfold("new")
    unfold("start")
    unfold("recordLast")
    unfold("badObserve")
    unfold("deliver")
    eliminate({"new": False, "start": False, "recordLast": False, "badObserve": False, "deliver": True})
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
    benchmark_info['name'] = 'crowds'
    benchmark_info['constant_defs'] = constant_defs

    for key, value in benchmark_info.items():
        print("{}: {}".format(key, value))

    return benchmark_info


if __name__ == "__main__":
    benchmark_info = crowds()
    print(to_latex_string(benchmark_info))
