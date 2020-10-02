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
