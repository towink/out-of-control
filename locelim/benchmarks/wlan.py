from locelim.interactive import *

if __name__ == "__main__":

    load_model("models/wlan.0.prism")
    show_model_constants()
    def_model_constant('COL', 2)
    show_orig_model_info()

    set_property("Pmax=? [ F col=COL ]")
    check_orig_model()

    # TODO try simplification
