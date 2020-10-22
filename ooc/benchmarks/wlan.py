from ooc.interactive import *
from ooc.models.files import wlan_0_prism

if __name__ == "__main__":

    load_model(wlan_0_prism)
    show_model_constants()
    def_model_constant('COL', 2)
    show_orig_model_info()

    set_property("Pmax=? [ F col=COL ]")
    check_orig_model()

    # TODO try simplification
