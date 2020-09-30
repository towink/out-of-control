from locelim.interactive import *
from locelim.interactive.commands import session, show_model_constants, set_property, load_model, def_model_constants, \
    check_orig_model, show_pcfp_stats, show_eliminable_locations, unfold, show_as_prism

if __name__ == "__main__":

    # comment out to disable logging
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

    load_model("originals/coin_game.prism")
    show_model_constants()
    set_property("P=? [ F x>=N ]")
    def_model_constants({'N': 100})

    res_orig = check_orig_model()

    unfold("f")
    show_eliminable_locations()
    session().get_loc_info()
    show_pcfp_stats()
    show_as_prism()

    model = session().build_model()
    session().check_model()
    print(model)
