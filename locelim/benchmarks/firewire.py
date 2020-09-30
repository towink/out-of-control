from locelim.interactive import *
from locelim.interactive.commands import session, show_model_constants, show_orig_model_info, set_property, load_model, \
    def_model_constants, check_orig_model, show_pcfp_stats, show_eliminable_locations, unfold

if __name__ == "__main__":
    # comment out to disable logging
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

    load_model("originals/firewire.false.prism")
    set_property('Pmin=? [ F (s1=8 & s2=7) | (s1=7 & s2=8) ]') # P>=1 [ F "done" ]

    show_model_constants()
    def_model_constants({'delay': 3, 'deadline': 200})
    show_orig_model_info()


    check_orig_model()

    show_pcfp_stats()

    unfold("x1")
    #unfold("w21")
    #unfold("s1")
    #unfold("s2")


    show_pcfp_stats()
    show_eliminable_locations()
    session().get_loc_info()

    print(session().build_model())
    session().check_model()
    #show_as_prism()

