import elmada
import matplotlib.pyplot as plt


def test_merit_order_plt():
    for method in ["PWL", "PP"]:
        plt.close()
        elmada.plots.merit_order_plt(year=2019, country="DE", method=method, include_histo=True)
        assert plt.gcf().number == 1
    plt.close()


def test_cefs_plt():
    for method in ["XEF_PWL", "MEF_PWL", "XEF_PP", "MEF_PWL"]:
        plt.close()
        elmada.plots.cefs_plt(year=2019, country="DE", method=method)
        assert plt.gcf().number == 1
    plt.close()
