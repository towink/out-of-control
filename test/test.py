from locelim.interactive import *


def assert_results_close(res_orig, res_other, epsilon=0.00001):
    if abs(res_orig - res_other) > epsilon:
        logging.error("original result: {}, simplified result: {}".format(res_orig, res_other))


if __name__ == '__main__':
    session().load_model("../locelim/benchmarks/originals/nand.prism")
    session().set_property("P=? [ F s=4 & z/N<0.1 ]")
    session().def_model_constants({'N': 10, 'K': 10})

    result_orig = session().check_orig_model()

    session().unfold("s")

    # eliminate a few locs and check result after each elimination
    session().eliminate({"s": 2})
    result_simplified = session().check_model()
    assert_results_close(result_orig, result_simplified)

    session().eliminate({"s": 3})
    result_simplified = session().check_model()
    assert_results_close(result_orig, result_simplified)

    session().eliminate({"s": 1})
    result_simplified = session().check_model()
    assert_results_close(result_orig, result_simplified)

    # try other constants
    session().def_model_constants({'N': 13, 'K': 5})

    result_orig = session().check_orig_model()
    result_simplified = session().check_model()
    assert_results_close(result_orig, result_simplified)

    # TODO: write more automated (!) tests here
    reset_session()
