from locelim.interactive import *

if __name__ == "__main__":

    # comment out to disable logging
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

    load_model("originals/leader_sync.5-3.prism")
    # P>=1 [ F "elected" ]
    set_property("P=? [ F s1=3&s2=3&s3=3&s4=3&s5=3 ]")

    show_orig_model_info()
    res_orig = check_orig_model()

    #show_as_prism()

    show_stats()

    unfold("s1")
    show_stats()
    show_eliminable_locations()
    eliminate_all()

    # unfold("s2")
    # unfold("s3")
    # unfold("s4")
    # unfold("s5")
    #unfold("p5")
    unfold("c")
    session()._pcfp.eliminate_unreachable()
    show_eliminable_locations()
    #eliminate_all()
    eliminate({"s1": 1, "c": 2})
    eliminate({"s1": 1, "c": 4})
    show_eliminable_locations()
    show_stats()

    #unfold("p5")
    # unfold("v1")
    # unfold("v2")
    # unfold("v3")
    # unfold("v4")
    # unfold("v5")
    #unfold("u1")

    show_stats()
    show_eliminable_locations()
    #eliminate_all()

    model = session().build_model()
    print(model)
    session().check_model()

