from locelim.interactive import *

from locelim.benchmarks.analyser import analyse_locations

if __name__ == "__main__":
    # comment out to disable logging
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

    load_model("originals/consensus.2.prism")
    show_model_constants()
    def_model_constant('K', 10)
    show_orig_model_info()

    # set_property('Pmin=? [ F "finished"&"all_coins_equal_1" ]')
    # TODO we cannot yet handle labels in property formulas
    set_property("Pmin=? [ F pc1=3 & pc2=3 & coin1=1 & coin2=1 ]")
    check_orig_model()

    show_stats()
    unfold('coin1')
    #unfold('pc2')

    show_eliminable_locations()
    #eliminate_all()

    show_stats()

    show_as_prism()
    model = session().build_model()
    print(model)
    session().check_model()

    #res = analyse_locations(session()._pcfp)
    #print(res)
    #show_as_prism()


