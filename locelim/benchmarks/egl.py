from locelim.interactive import *

if __name__ == "__main__":
    # comment out to disable logging
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

    load_model("originals/egl.prism")
    show_model_constants()
    def_model_constants({'N': 5, 'L': 2})
    show_orig_model_info()

    set_property('P =? [F !( (b0=L & b5=L) | (b1=L & b6=L) | (b2=L & b7=L) | (b3=L & b8=L) | (b4=L & b9=L)) &\
                           ( (a0=L & a5=L) | (a1=L & a6=L) | (a2=L & a7=L) | (a3=L & a8=L) | (a4=L & a9=L))]')
    set_property('P=? [ F !"kA" & "kB" ]')
    check_orig_model()
