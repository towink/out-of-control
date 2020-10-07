from locelim.interactive import *

if __name__ == "__main__":

    # comment out to disable logging
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

    load_model("originals/phil3.prism")

    # I made this property up
    set_property("Pmax=? [ F ((p1>=8)&(p1<=9))|((p2>=8)&(p2<=9))|((p3>=8)&(p3<=9)) ]")


    show_orig_model_info()
    check_orig_model()


    show_pcfp_stats()

    unfold("p1")
    show_eliminable_locations()
    session().eliminate_unsatisfiable_commands()

    model = session().build_model()
    print(model)
    print(session().check_model())

