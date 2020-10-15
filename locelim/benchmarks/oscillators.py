from locelim.interactive import *

if __name__ == "__main__":
    # uncomment to disable logging
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

    load_model("models/oscillators.6-10-0.1-1.prism")
    #def_model_constants({"mu" :0.1, "lambda": 1})


    unit_vector_x_1 = "1.000000000000"
    unit_vector_y_1 = "0.000000000000"
    unit_vector_x_2 = "0.500000000000"
    unit_vector_y_2 = "0.866025403784"
    unit_vector_x_3 = "-0.500000000000"
    unit_vector_y_3 = "0.866025403784"
    unit_vector_x_4 = "-1.000000000000"
    unit_vector_y_4 = "0.000000000000"
    unit_vector_x_5 = "-0.500000000000"
    unit_vector_y_5 = "-0.866025403784"
    unit_vector_x_6 = "0.500000000000"
    unit_vector_y_6 = "-0.866025403784"
    unit_vector_x_avg_squared = f"pow(((({unit_vector_x_1} * k_1) " \
                                f"+ ({unit_vector_x_2} * k_2) " \
                                f"+ ({unit_vector_x_3} * k_3) " \
                                f"+ ({unit_vector_x_4} * k_4) " \
                                f"+ ({unit_vector_x_5} * k_5) " \
                                f"+ ({unit_vector_x_6} * k_6)) / 6), 2)"
    unit_vector_y_avg_squared = f"pow(((({unit_vector_y_1} * k_1) " \
                                f"+ ({unit_vector_y_2} * k_2) " \
                                f"+ ({unit_vector_y_3} * k_3) " \
                                f"+ ({unit_vector_y_4} * k_4) " \
                                f"+ ({unit_vector_y_5} * k_5) " \
                                f"+ ({unit_vector_y_6} * k_6)) / 6), 2)"
    order_parameter = f"pow({unit_vector_x_avg_squared} + {unit_vector_y_avg_squared}, 0.5)"
    lamb = "1"
    set_property(f"Pmax=? [ F {order_parameter} >= {lamb } ]")


    show_orig_model_info()
    #check_orig_model()


    show_pcfp_stats()

    unfold("k_1")
    #session().eliminate_unsatisfiable_commands()
    #eliminate_all()
    unfold("k_2")
    unfold("k_3")
    unfold("k_4")
    #show_as_prism()
    # unfold("k_2")
    # unfold("k_3")
    #unfold("k_4")
    #unfold("k_5")
    #print(session()._pcfp.get_lucky_locs())
    show_eliminable_locations()

    model = session().build_model()
    print(model)
    print(session().check_model())

