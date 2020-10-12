from locelim.interactive import *

if __name__ == "__main__":
    # comment out to disable logging
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

    load_model("originals/consensus.4.manual.prism")
    show_model_constants()
    def_model_constant('K', 10)
    show_orig_model_info()

    # set_property('Pmin=? [ F "finished"&"all_coins_equal_1" ]')
    # TODO we cannot yet handle labels in property formulas
    #set_property("Pmin=? [ F pc1=3 & pc2=3 & coin1=1 & coin2=1]")
    set_property("Pmin=? [ F pc1=3 & pc2=3 & pc3=3 & pc4=3 & coin1=1 & coin2=1 & coin3=1 & coin4=1 ]")
    #set_property("Pmin=? [ F pc1=3 & pc2=3 & pc3=3 & pc4=3 & pc5=3 & pc6=3 & coin1=1 & coin2=1 & coin3=1 & coin4=1 & coin5=1 & coin6=1 ]")
    #set_property("Pmin=? [ F 0=1 ]")
    check_orig_model()

    # show_pcfp_stats()
    #unfold('pc1')
    #
    #show_as_prism()
    # show_eliminable_locations()
    #eliminate_all()
    #show_as_prism()
    # session()._pcfp.remove_duplicate_cmds()
    # unfold('pc2')
    #
    # show_pcfp_stats()
    #
    # #show_eliminable_locations()
    # #eliminate_all()
    # eliminate({"pc1": 3, "pc2": 0})
    #
    # #show_eliminable_locations()
    # eliminate({"pc1": 0, "pc2": 3})
    # #show_eliminable_locations()
    #
    # eliminate({"pc1": 1, "pc2": 0})
    # eliminate({"pc1": 0, "pc2": 1})
    # #show_eliminable_locations()
    #
    # eliminate({"pc1": 3, "pc2": 2})
    # eliminate({"pc1": 2, "pc2": 3})
    # #show_eliminable_locations()
    #
    # eliminate({"pc1": 0, "pc2": 2})
    # eliminate({"pc1": 2, "pc2": 0})
    # #show_eliminable_locations()
    #
    # eliminate({"pc1": 2, "pc2": 2})
    # #show_eliminable_locations()


    #show_loc_info()

    #show_pcfp_stats()



    show_pcfp_stats()

    #show_as_prism()
    model = session().build_model()
    print(model)
    #session().check_model()

    #res = analyse_locations(session()._pcfp)
    #print(res)
    #show_as_prism()


