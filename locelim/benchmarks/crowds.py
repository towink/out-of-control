from locelim.interactive import *

if __name__ == "__main__":
    # comment out to disable logging
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

    load_model("originals/crowds.prism")
    set_property('P=? [ F observe0>1  ]')

    show_model_constants()
    def_model_constants({'TotalRuns': 5, 'CrowdSize': 2})  # crowd size can only be 2,4,5,10,15,20
    show_orig_model_info()



    check_orig_model()

    show_pcfp_stats()
    # unfold("launch")
    # unfold("new")
    # unfold("start")
    # unfold("run")
    #unfold("lastSeen")

    #unfold("good")
    # unfold("bad")
    unfold("recordLast")
    unfold("badObserve")
    unfold("deliver")
    # unfold("done")
    show_loc_info()
    show_as_prism()
    print(session()._pcfp.get_lucky_locs())
    print(session()._pcfp.get_sink_locs_without_targets(session()._get_goal_predicate()))

    show_pcfp_stats()
    session()._pcfp.eliminate_nop_selfloops()
    show_eliminable_locations()

    print(session().build_model())

    #show_as_prism()
