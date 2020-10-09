from locelim.interactive import *
from locelim.benchmarks.benchmark_utils import to_latex_string, stat_vars


def coupon(constant_defs=None):
    reset_session()

    # comment out to disable logging
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

    #load_model("originals/coupon_count.10-1.prism")
    load_model("originals/coupon.10-1.prism")
    if constant_defs is None:
        #constant_defs = {"N": 10}
        constant_defs = {}
    def_model_constants(constant_defs)
    set_property("P=? [ F c0 & c1 & c2 & c3 & c4 & c5 & c6 & c7 & c8 & c9 & s=2]")
    #set_property("P=? [ F c0 & c1 & c2 & c3 & c4 & c5 & c6 & c7 & c8 & c9 & s=2 & c=N]")

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
    session().unfold("s")
    eliminate({"s": 1})
    unfold("draw")
    eliminate_all()
    #unfold("c0")
    #eliminate_all()
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

    print("result orig: {}".format(res_orig))
    print("result simpl: {}".format(res_simpl))

    local_vars = locals()
    benchmark_info = dict([(var, local_vars[var]) for var in stat_vars])
    benchmark_info['name'] = 'coupon'
    benchmark_info['constant_defs'] = {"coupons": 10, "draws": 1}

    for key, value in benchmark_info.items():
        print("{}: {}".format(key, value))

    return benchmark_info


if __name__ == "__main__":
    benchmark_info = coupon()
    print(to_latex_string(benchmark_info))
