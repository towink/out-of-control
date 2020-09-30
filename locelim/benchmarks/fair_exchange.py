from locelim.interactive import *

if __name__ == "__main__":

    # comment out to disable logging
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

    load_model("originals/fair_exchange.prism")
    show_model_constants()
    # ATTENTION: I added turn=1 to the property to restrict the potential goals, seems to make no difference
    set_property("Pmax=?[F (i>0) & (mA>=i) & (mB<i) & turn=1]")

    res_orig = check_orig_model()
    show_orig_model_info()
    show_as_prism()

    unfold("d")
    unfold("turn")
    #unfold("i")  # there is a bug when unfolding i
    show_eliminable_locations()
    session().show_loc_info()
    eliminate_all()
    show_as_prism()


    show_stats()
    #show_as_prism()

    model = session().build_model()
    session().check_model()
    print(model)