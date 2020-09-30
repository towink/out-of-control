from locelim.interactive import *

if __name__ == "__main__":

    # comment out to disable logging
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

    load_model("originals/oscillators.6-6-0.1-1.prism")
    #def_model_constants({"mu" :0.1, "lambda": 1})

    # I made this property up
    #set_property("Pmax=? [ F ((p1>=8)&(p1<=9))|((p2>=8)&(p2<=9))|((p3>=8)&(p3<=9)) ]")


    show_orig_model_info()
    #check_orig_model()


    show_pcfp_stats()

    unfold("k_1")
    #show_as_prism()
    unfold("k_2")
    #unfold("k_3")
    #unfold("k_4")
    #unfold("k_5")
    show_loc_info()
    show_eliminable_locations()
    session()._pcfp.eliminate_nop_selfloops()

    model = session().build_model()
    print(model)
    print(session().check_model())

