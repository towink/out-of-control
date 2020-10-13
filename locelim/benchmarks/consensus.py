from locelim.interactive import *

import stormpy as sp

if __name__ == "__main__":
    # comment out to disable logging
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)

    #session().load_composition("originals/consensus.2.prism")

    session().load_model("originals/consensus.2.manual.prism")
    print(session().get_model_constants())
    session().def_model_constant('K', 2)
    session().set_property("Pmin=? [ F pc1=3 & pc2=3 & coin1=1 & coin2=1]")
    print(session().build_orig_model())
    #print(session().check_orig_model())
    session().build_model()
    session().unfold("pc1")
    session().unfold("pc2")
    print(list(session().eliminable_locs()))

    #session().eliminate({"pc1": 2})
    session().eliminate_all()

    print(session().build_model())
    print(session().check_orig_model())
    print(session().check_model())


    # prism_model = sp.parse_prism_program("originals/consensus.2.prism")
    # comp = PCFPComposition.from_prism(prism_model)
    # mgr: sp.ExpressionManager = comp.expression_manager
    # proc1 = comp.get_module_by_name("process1")
    # proc1.unfold(mgr.get_variable("pc1"))
    # print(comp.to_prism_string())
    # print(list(proc1.eliminable_locs("pc1=3 & pc2=3 & coin1=1 & coin2=1")))
    #
    #
    # load_model("originals/consensus.2.prism")
    # show_model_constants()
    # def_model_constant('K', 10)
    # show_orig_model_info()
    #
    # # set_property('Pmin=? [ F "finished"&"all_coins_equal_1" ]')
    # # TODO we cannot yet handle labels in property formulas
    # set_property("Pmin=? [ F pc1=3 & pc2=3 & coin1=1 & coin2=1]")
    # #set_property("Pmin=? [ F pc1=3 & pc2=3 & pc3=3 & pc4=3 & coin1=1 & coin2=1 & coin3=1 & coin4=1 ]")
    # #set_property("Pmin=? [ F pc1=3 & pc2=3 & pc3=3 & pc4=3 & pc5=3 & pc6=3 & coin1=1 & coin2=1 & coin3=1 & coin4=1 & coin5=1 & coin6=1 ]")
    # #set_property("Pmin=? [ F 0=1 ]")
    # check_orig_model()

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



    #show_pcfp_stats()

    #show_as_prism()
    #model = session().build_model()
    #print(model)
    #session().check_model()

    #res = analyse_locations(session()._pcfp)
    #print(res)
    #show_as_prism()


