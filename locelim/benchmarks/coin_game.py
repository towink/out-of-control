from locelim.interactive import *

if __name__ == "__main__":

    # comment out to disable logging
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

    load_model("originals/coin_game.prism")
    show_model_constants()
    set_property("P=? [ F x>=N ]")
    def_model_constants({'N': 1000})

    res_orig = check_orig_model()
    show_orig_model_info()

    unfold("f")
    show_eliminable_locations()
    show_loc_info()
    eliminate({"f": True})  # this locatino is lucky so eliminate it
    show_pcfp_stats()
    show_as_prism()

    model = session().build_model()
    session().check_model()
    print(model)

from locelim.benchmarks.benchmark_utils import to_latex_string, stat_vars
from locelim.interactive import *


# manual analysis/benchmarking of the coin game from the paper

def coin_game(constant_defs=None):
    reset_session()

    # comment out to disable logging
    # logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

    load_model("originals/coin_game.prism")
    show_model_constants()
    set_property("P=? [ F x>=N ]")
    if constant_defs is None:
        constant_defs = {'N': 1000}
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
    session().unfold("f")
    session().eliminate({"f": True})  # this location is lucky so eliminate it
    #session().eliminate_unsatisfiable_commands()
    #session().eliminate_all()
    # end of simplificaiton

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
    benchmark_info['name'] = 'coin'
    benchmark_info['constant_defs'] = constant_defs

    for key, value in benchmark_info.items():
        print("{}: {}".format(key, value))

    return benchmark_info


if __name__ == "__main__":
    benchmark_info = coin_game()
    print(to_latex_string(benchmark_info))
