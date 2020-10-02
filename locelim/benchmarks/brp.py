from locelim.interactive import *
from locelim.benchmarks.analyser import analyse_locations
from locelim.benchmarks.benchmark_utils import to_latex_string

# def bluetooth_manual_simplification():
#     prism_program: sp.PrismProgram = sp.parse_prism_program("originals/brp.prism")
#     prism_props = sp.parse_properties_for_prism_program("P=? [ F s=5 ]",
#                                                         prism_program)  # These props probably don't make sense for bluetooth?
#     jani_model, jani_props = prism_program.to_jani(prism_props)
#     jani_model = jani_model.flatten_composition()
#
#     # start simplifying the model, convert to pcfp first
#     # here we leave undef constants undefined
#     pcfp = PCFP.from_jani(jani_model)
#
#     mgr: sp.ExpressionManager = pcfp.get_manager()
#
#     # prism_defined = prism_program.define_constants({mgr.get_variable("N"): mgr.create_integer(16),
#     #                                 mgr.get_variable("MAX"): mgr.create_integer(2)})
#     # model = sp.build_model(prism_defined, prism_props)
#     # print("number of states: {}".format(len(model.states)))
#
#     r = mgr.get_variable("r")
#     s = mgr.get_variable("s")
#     k = mgr.get_variable("k")
#     l = mgr.get_variable("l")
#
#     locelim.interactive.commands.unfold(r)
#     locelim.interactive.commands.unfold(s)
#
#
#     # locs_to_eliminate = [{r: mgr.create_integer(1), s: mgr.create_integer(i)} for i in range(1, 5)]
#
#     print(str(len(pcfp.get_locs())) + " Locations after unfolding r and s")
#     pcfp.eliminate_unreachable()
#     print(str(len(pcfp.get_locs())) + " Locations after eliminating unreachable")
#     eliminate_locations(41, pcfp, 100)
#     print(str(len(pcfp.get_locs())) + " Locations after elimination")
#
#     locelim.interactive.commands.unfold(k)
#     print(str(len(pcfp.get_locs())) + " Locations after unfolding k")
#     pcfp.eliminate_unreachable()
#     print(str(len(pcfp.get_locs())) + " Locations after eliminating unreachable")
#     eliminate_locations(len(pcfp.get_locs()) - 1, pcfp, 500)
#     print(str(len(pcfp.get_locs())) + " Locations after elimination")
#
#     locelim.interactive.commands.unfold(l)
#     print(str(len(pcfp.get_locs())) + " Locations after unfolding l")
#     pcfp.eliminate_unreachable()
#     print(str(len(pcfp.get_locs())) + " Locations after eliminating unreachable")
#     eliminate_locations(len(pcfp.get_locs()) - 1, pcfp, 5000)
#     print(str(len(pcfp.get_locs())) + " Locations after elimination")
#
#
#
#     # analyse_potential_unfolds(pcfp)
#
#     # analyse_potential_unfolds(pcfp)
#
#     # analyse_locations(pcfp)
#
#     # pcfp.eliminate_nop_selfloops()
#
#     # print(pcfp.to_prism_string())
#
#
# def eliminate_locations(max_tries, pcfp, new_transition_cutoff):
#     for i in range(max_tries):
#         best_loc = analyse_locations(pcfp, silent=True, max_new_transitions=new_transition_cutoff)
#         if best_loc is None:
#             print(
#                 "No more locations can be eliminated (or eliminating more locations would create too many transitions")
#             break
#
#         print("Eliminating " + str(best_loc))
#         pcfp.eliminate_loc(best_loc, silent=True)

def brp():
    # comment out to disable logging
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

    load_model("originals/brp.prism")
    show_model_constants()
    set_property("P=? [ F s=5 & srep=2 ]")
    constant_defs = {"N": 1000, "MAX": 20}
    def_model_constants(constant_defs)

    model_orig, time_build_orig = session().build_orig_model(return_time=True)
    res_orig, time_check_orig = session().check_orig_model(return_time=True)
    states_orig = len(model_orig.states)
    transitions_orig = model_orig.nr_transitions

    t_start = time.time()

    # actual simplification starts here
    session().unfold("r")
    session().unfold("s")
    session().eliminate_all()
    session().eliminate({"r":2 , "s": 6})  # this location is "lucky", it has self loop but can be eliminated
    session().unfold("l")
    session().unfold("k")
    session().eliminate_all()
    session().unfold("srep")
    session().eliminate_all()
    session().unfold("s_ab")
    session().eliminate_all()

    t_end = time.time()
    time_simplification = t_end - t_start

    model_simpl, time_build_simpl = session().build_model(return_time=True)
    res_simpl, time_check_simpl = session().check_model(return_time=True)
    states_simpl = len(model_simpl.states)
    transitions_simpl = model_simpl.nr_transitions

    print("result orig: {}".format(res_orig))
    print("result simpl: {}".format(res_simpl))

    # collect info for benchmark table

    stat_vars = ['states_orig', 'transitions_orig',
                 'states_simpl', 'transitions_simpl',
                 'time_build_orig', 'time_build_simpl',
                 'time_check_orig', 'time_check_simpl',
                 'time_simplification']
    local_vars = locals()
    benchmark_info = dict([(var, local_vars[var]) for var in stat_vars])
    benchmark_info['name'] = 'brp'
    benchmark_info['constant_defs'] = constant_defs
    for key, value in benchmark_info.items():
        print("{}: {}".format(key, value))

    return benchmark_info


if __name__ == "__main__":
    benchmark_info = brp()
    #print(to_latex_string(benchmark_info))
