from locelim.benchmarks.benchmark_utils import stat_vars
from locelim.interactive import *


def egl(constant_defs=None):
    reset_session()

    load_model("models/egl.prism")
    # TODO labels in properties not yet supported, so here's a workaround
    L = 2
    kB = f"( (a0={L}  & a20={L})\
    			 | (a1={L}  & a21={L})\
    			 | (a2={L}  & a22={L})\
    			 | (a3={L}  & a23={L})\
    			 | (a4={L}  & a24={L})\
    			 | (a5={L}  & a25={L})\
    			 | (a6={L}  & a26={L})\
    			 | (a7={L}  & a27={L})\
    			 | (a8={L}  & a28={L})\
    			 | (a9={L}  & a29={L})\
    			 | (a10={L} & a30={L})\
    			 | (a11={L} & a31={L})\
    			 | (a12={L} & a32={L})\
    			 | (a13={L} & a33={L})\
    			 | (a14={L} & a34={L})\
    			 | (a15={L} & a35={L})\
    			 | (a16={L} & a36={L})\
    			 | (a17={L} & a37={L})\
    			 | (a18={L} & a38={L})\
    			 | (a19={L} & a39={L}))"
    kA = f"( (b0={L}  & b20={L})\
    			 | (b1={L}  & b21={L})\
    			 | (b2={L}  & b22={L})\
    			 | (b3={L}  & b23={L})\
    			 | (b4={L}  & b24={L})\
    			 | (b5={L}  & b25={L})\
    			 | (b6={L}  & b26={L})\
    			 | (b7={L}  & b27={L})\
    			 | (b8={L}  & b28={L})\
    			 | (b9={L}  & b29={L})\
    			 | (b10={L} & b30={L})\
    			 | (b11={L} & b31={L})\
    			 | (b12={L} & b32={L})\
    			 | (b13={L} & b33={L})\
    			 | (b14={L} & b34={L})\
    			 | (b15={L} & b35={L})\
    			 | (b16={L}& b36={L})\
    			 | (b17={L} & b37={L})\
    			 | (b18={L} & b38={L})\
    			 | (b19={L} & b39={L}))"
    set_property('P=? [ F (!{} & {} & phase=4)  ]'.format(kA, kB))
    if constant_defs is None:
        constant_defs = {'N': 5, 'L': L}
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

    # start of simplification
    flatten()
    unfold("phase")
    unfold("party")
    eliminate_all()
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
    benchmark_info['name'] = 'egl'
    benchmark_info['constant_defs'] = constant_defs

    for key, value in benchmark_info.items():
        print("{}: {}".format(key, value))

    return benchmark_info


if __name__ == "__main__":
    # uncomment to disable logging
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
    egl()
