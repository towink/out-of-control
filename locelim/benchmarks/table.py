from locelim.benchmarks.benchmark_utils import to_latex_string
from locelim.benchmarks.brp import brp
from locelim.benchmarks.coin_game import coin_game
from locelim.benchmarks.coupon import coupon
from locelim.benchmarks.nand import nand


def make_latex_table():
    res = ""

    benchmark_info = nand({"N": 40, "K": 4})
    res += to_latex_string(benchmark_info)

    benchmark_info = nand({"N": 60, "K": 2})
    res += to_latex_string(benchmark_info)

    benchmark_info = brp({"N": 2048, "MAX": 10})
    res += to_latex_string(benchmark_info)

    benchmark_info = brp({"N": 4096, "MAX": 20})
    res += to_latex_string(benchmark_info)

    benchmark_info = coupon({"N": 10})
    res += to_latex_string(benchmark_info)

    benchmark_info = coupon({"N": 100})
    res += to_latex_string(benchmark_info)

    benchmark_info = coin_game({"N": 10000})
    res += to_latex_string(benchmark_info)

    return res

if __name__ == "__main__":
    table = make_latex_table()
    print(table)
