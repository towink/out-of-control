from locelim.interactive import *

if __name__ == "__main__":

    # comment out to disable logging
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

    load_model("originals/leader_sync.4-8.prism")

    # P>=1 [ F "elected" ]
    #set_property("P=? [ F s1=3&s2=3&s3=3 ]")  # for 3-x
    set_property("P=? [ F s1=3&s2=3&s3=3&s4=3 ]")  # for 4-x
    # set_property("P=? [ F s1=3&s2=3&s3=3&s4=3&s5=3 ]")  # for 5-x
    # set_property("P=? [ F s1=3&s2=3&s3=3&s4=3&s5=3&s6=3 ]")  # for 6-x


    show_orig_model_info()
    check_orig_model()


    show_pcfp_stats()

    unfold("s1")
    #show_eliminable_locations()
    eliminate_all()
    #show_pcfp_stats()

    unfold("c")
    #show_eliminable_locations()
    eliminate({"s1": 1, "c": 2})
    #show_eliminable_locations()
    show_loc_info()
    session().eliminate_unsatisfiable_commands()

    show_pcfp_stats()

    model = session().build_model()
    print(model)
    print(session().check_model())
