from locelim.interactive import *

if __name__ == "__main__":
    # comment out to disable logging
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

    load_model("originals/egl.prism")
    show_model_constants()
    # def_model_constants({'N': 5, 'L': 2})
    def_model_constants({'N': 5})
    show_orig_model_info()

    # set_property('P=? [ F !"kA" & "kB" ]')
    L = 4
    kB = f"( (a0={L}  & a20={L})\
			 | (a1={L}  & a21={L})\
			 | (a2={L}  & a22={L})\
			 | (a3={L}  & a23={L})\
			 | (a4={L}  & a24={L})\
			 | (a5={L}  & a25={L})\
			 | (a6={L}  & a26={L})\
			 | (a7={L}  & a27={L})\
			 | (a8={L}  & a28={L})\
			 | (a9={L}  & a29={L})\
			 | (a10={L} & a30={L})\
			 | (a11={L} & a31={L})\
			 | (a12={L} & a32={L})\
			 | (a13={L} & a33={L})\
			 | (a14={L} & a34={L})\
			 | (a15={L} & a35={L})\
			 | (a16={L} & a36={L})\
			 | (a17={L} & a37={L})\
			 | (a18={L} & a38={L})\
			 | (a19={L} & a39={L}))"

    kA = f"( (b0={L}  & b20={L})\
			 | (b1={L}  & b21={L})\
			 | (b2={L}  & b22={L})\
			 | (b3={L}  & b23={L})\
			 | (b4={L}  & b24={L})\
			 | (b5={L}  & b25={L})\
			 | (b6={L}  & b26={L})\
			 | (b7={L}  & b27={L})\
			 | (b8={L}  & b28={L})\
			 | (b9={L}  & b29={L})\
			 | (b10={L} & b30={L})\
			 | (b11={L} & b31={L})\
			 | (b12={L} & b32={L})\
			 | (b13={L} & b33={L})\
			 | (b14={L} & b34={L})\
			 | (b15={L} & b35={L})\
			 | (b16={L}& b36={L})\
			 | (b17={L} & b37={L})\
			 | (b18={L} & b38={L})\
			 | (b19={L} & b39={L}))"

    set_property('P=? [ F (!{} & {} & phase=4)  ]'.format(kA, kB))
    check_orig_model()

    show_stats()
    unfold("phase")
    unfold("party")
    unfold("b")
    session()._pcfp.eliminate_nop_selfloops()
    show_eliminable_locations()
    show_stats()
    session().show_loc_info()
    #show_as_prism()

    model = session().build_model()
    print(model)
    session().check_model()
