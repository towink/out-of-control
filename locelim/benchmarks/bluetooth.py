from locelim.benchmarks.benchmark_utils import to_latex_string, stat_vars
from locelim.interactive import *


# manual analysis/benchmarking of bluetooth

def bluetooth(constant_defs=None):
    reset_session()

    # comment out to disable logging
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

    load_model("originals/bluetooth.prism")
    set_property("P=? [ F 0=1 ]")
    # if constant_defs is None:
    #     constant_defs = {'mrec': 1}
    # def_model_constants(constant_defs)

    # model_orig, time_build_orig = session().build_orig_model(return_time=True)
    # res_orig, time_check_orig = session().check_orig_model(return_time=True)
    # states_orig = model_orig.nr_states
    # transitions_orig = model_orig.nr_transitions

    show_as_prism()  # TODO beaks with SIGSEGV

    pcfp_stats = session().get_pcfp_stats()
    orig_locs = pcfp_stats["locations"]
    orig_cmds = pcfp_stats["commands"]
    orig_trans = pcfp_stats["transitions"]

    t_start = time.time()

    # actual simplification starts here
    show_pcfp_stats()
    #unfold("f1")
    # unfold("t1")
    # unfold("train1")
    #unfold("freq1")

    unfold("receiver")
    unfold("send")
    unfold("rec")

    show_loc_info()
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
    benchmark_info['name'] = 'nand'
    benchmark_info['constant_defs'] = constant_defs

    for key, value in benchmark_info.items():
        print("{}: {}".format(key, value))

    return benchmark_info


if __name__ == "__main__":
    benchmark_info = bluetooth()
    print(to_latex_string(benchmark_info))
