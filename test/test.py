from locelim.interactive import *


# this file contains automated tests


def assert_results_close(res_orig, res_other, epsilon=0.0001):
    if abs(res_orig - res_other) > epsilon:
        logging.error("original result: {}, simplified result: {}".format(res_orig, res_other))


if __name__ == '__main__':
    models_folder = "../locelim/benchmarks/models/"

    # --- test with nand ---

    load_model("{}nand.prism".format(models_folder))
    set_property("P=? [ F s=4 & z/N<0.1 ]")
    def_model_constants({'N': 10, 'K': 10})

    result_orig = session().check_orig_model()

    unfold("s")

    # eliminate a few locs and check result after each elimination
    eliminate({"s": 2})
    result_simplified = session().check_model()
    assert_results_close(result_orig, result_simplified)

    eliminate({"s": 3})
    result_simplified = session().check_model()
    assert_results_close(result_orig, result_simplified)

    eliminate({"s": 1})
    result_simplified = session().check_model()
    assert_results_close(result_orig, result_simplified)

    # try other constants
    def_model_constants({'N': 13, 'K': 5})

    result_orig = session().check_orig_model()
    result_simplified = session().check_model()
    assert_results_close(result_orig, result_simplified)

    print("nand test complete")
    reset_session()

    # --- test with brp ---

    load_model("{}brp.prism".format(models_folder))
    def_model_constants({"N": 32, "MAX": 4})
    set_property("P=? [ F s=5 & srep=2 ]")

    result_orig = session().check_orig_model()

    flatten()  # brp contains several modules

    unfold("r")
    result_simplified = session().check_model()
    assert_results_close(result_orig, result_simplified)

    unfold("k")
    unfold("l")
    result_simplified = session().check_model()
    assert_results_close(result_orig, result_simplified)

    unfold("s")
    eliminate({"r": 4, "k": 0, "l": 0, "s": 3})
    result_simplified = session().check_model()
    assert_results_close(result_orig, result_simplified)

    print("brp test complete")
    reset_session()

    # TODO: write more automated (!) tests here
