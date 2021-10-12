import matplotlib.pyplot as plt
import elmada


def test_merit_order():
    for method in ["PWL", "PP"]:
        plt.close()
        elmada.plots.merit_order(year=2019, country="DE", method=method, include_histo=True)
        assert plt.gcf().number == 1
    plt.close()


def test_cefs_scatter():
    for method in ["XEF_PWL", "MEF_PWL", "XEF_PP", "MEF_PWL"]:
        plt.close()
        elmada.plots.cefs_scatter(year=2019, country="DE", method=method)
        assert plt.gcf().number == 1
    plt.close()


def test_cef_country_map():
    elmada.plots.cef_country_map(year=2019, method="XEF_PWL", scope="Europe20")


def test_cefs_scatter_plotly():
    elmada.plots.cefs_scatter_plotly(year=2019, freq="60min", country="DE", method="MEF_PWL")
