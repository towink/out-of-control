from locelim.interactive import *

from locelim.interactive.commands import session, show_model_constants, show_orig_model_info, set_property, load_model, \
    def_model_constant, check_orig_model, show_pcfp_stats, eliminate, show_eliminable_locations, unfold, show_as_prism

if __name__ == "__main__":
    # comment out to disable logging
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

    load_model("originals/wlan.0.v1.prism")
    show_model_constants()
    def_model_constant('COL', 0)
    show_orig_model_info()

    set_property("Pmax=? [ F col=COL ]")
    check_orig_model()

    show_pcfp_stats()
    # unfold('pc1')
    # unfold('pc2')
    #
    # show_pcfp_stats()
    #
    # show_eliminable_locations()
    # #eliminate_all()
    # eliminate({"pc1": 3, "pc2": 0})
    #
    # show_eliminable_locations()
    # eliminate({"pc1": 0, "pc2": 3})
    # show_eliminable_locations()
    #
    # eliminate({"pc1": 1, "pc2": 0})
    # eliminate({"pc1": 0, "pc2": 1})
    # show_eliminable_locations()
    #
    # eliminate({"pc1": 3, "pc2": 2})
    # eliminate({"pc1": 2, "pc2": 3})
    # show_eliminable_locations()
    #
    # eliminate({"pc1": 0, "pc2": 2})
    # eliminate({"pc1": 2, "pc2": 0})
    # show_eliminable_locations()
    #
    # eliminate({"pc1": 2, "pc2": 2})
    # show_eliminable_locations()

    # session().get_loc_info()
    #
    # show_pcfp_stats()
    # session()._pcfp.remove_duplicate_cmds()
    #
    #
    # show_pcfp_stats()

    show_as_prism()
    model = session().build_model()
    print(model)
    session().check_model()

    #res = analyse_locations(session()._pcfp)
    #print(res)
    #show_as_prism()

