from ooc.interactive import *
from ooc.models.files import firewire_dl_prism, firewire_false_prism

if __name__ == "__main__":
    # comment out to disable logging
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

    load_model(firewire_dl_prism)
    #set_property('Pmin=? [ F (s1=8 & s2=7) | (s1=7 & s2=8) ]') # P>=1 [ F "done" ]
    set_property('Pmin=? [ F s=9 ]')  # for firewire_dl

    show_model_constants()
    def_model_constants({'delay': 3, 'deadline': 200})
    show_orig_model_info()


    check_orig_model()

    show_pcfp_stats()

    unfold("s")
    unfold("x")
    show_loc_info()
    session().eliminate_unsatisfiable_commands()
    session().eliminate_all(50)
    #unfold("w21")
    #unfold("s1")
    #unfold("s2")


    show_pcfp_stats()
    show_eliminable_locations()
    session().get_loc_info()

    print(session().build_model())
    session().check_model()
    #show_as_prism()
