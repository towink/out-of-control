from locelim.interactive import *
from locelim.interactive.commands import session, show_model_constants, show_orig_model_info, set_property, load_model, \
    def_model_constants, check_orig_model, show_pcfp_stats, show_eliminable_locations, unfold

if __name__ == "__main__":
    # comment out to disable logging
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

    load_model("originals/crowds.prism")
    set_property('P=? [ F observe0>1  ]')

    show_model_constants()
    def_model_constants({'TotalRuns': 3, 'CrowdSize': 5})
    show_orig_model_info()



    check_orig_model()

    show_pcfp_stats()
    #unfold("launch")
    #unfold("new")
    # unfold("start")
    # unfold("run")
    unfold("lastSeen")

    #session()._pcfp.get_lucky_locs()
    unfold("good")
    unfold("bad")
    unfold("recordLast")
    unfold("badObserve")
    #unfold("deliver")
    #unfold("done")
    session().get_loc_info()

    show_pcfp_stats()
    session()._pcfp.eliminate_nop_selfloops()
    show_eliminable_locations()

    print(session().build_model())

    #show_as_prism()



