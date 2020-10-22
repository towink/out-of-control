from locelim.benchmarks.benchmark_utils import to_latex_string
from locelim.benchmarks.brp import brp
from locelim.benchmarks.coin_game import coin_game
from locelim.benchmarks.coupon import coupon
from locelim.benchmarks.crowds import crowds
from locelim.benchmarks.egl import egl
from locelim.benchmarks.leader_sync import leader_sync
from locelim.benchmarks.nand import nand


def make_latex_table_tacas_21_submission():
    res = "\\documentclass[11pt,a4paper,landscape]{article}\n"
    res += "\\usepackage{graphicx}\n"
    res += "\\begin{document}\n"
    res += "\\begin{scriptsize}\n"
    res += "\\begin{tabular}{r l | r  r | r  r | r  r | r  r | r | r  r}\n"
    res += "Name & Consts. & States &  & Trans. & & Build & & Check & & Red. & PCFP trans. & \\\\ \n"
    res += " &  & orig. & red. & orig. & red. & orig. & red. & orig. & red. &  & orig. & red. \\\\ \n"
    res += "\\hline\n"

    benchmark_info = brp({"N": 2**11, "MAX": 10})
    res += to_latex_string(benchmark_info)
    benchmark_info = brp({"N": 2**12, "MAX": 20})
    res += to_latex_string(benchmark_info)

    res += "\\hline\n"

    benchmark_info = coupon()
    res += to_latex_string(benchmark_info)

    res += "\\hline\n"

    benchmark_info = crowds({'TotalRuns': 5, 'CrowdSize': 5})
    res += to_latex_string(benchmark_info)
    benchmark_info = crowds({'TotalRuns': 10, 'CrowdSize': 5})
    res += to_latex_string(benchmark_info)

    res += "\\hline\n"

    benchmark_info = egl()
    res += to_latex_string(benchmark_info)

    res += "\\hline\n"

    benchmark_info = leader_sync()
    res += to_latex_string(benchmark_info)

    res += "\\hline\n"

    benchmark_info = nand({"N": 40, "K": 4})
    res += to_latex_string(benchmark_info)
    benchmark_info = nand({"N": 60, "K": 2})
    res += to_latex_string(benchmark_info)

    res += "\\hline\n"

    benchmark_info = coin_game({"N": 10000})
    res += to_latex_string(benchmark_info)

    res += "\\end{tabular}\n"
    res += "\\end{scriptsize}\n"
    res += "\\end{document}\n"

    return res

if __name__ == "__main__":
    table = make_latex_table_tacas_21_submission()
    with open("table.tex", "w") as f:
        f.write(table)
