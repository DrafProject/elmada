import elmada

fig = elmada.plots.cef_country_map(year=2020, method="XEF_EP")
fp = elmada.paths.BASE_DIR.parent / "doc/images/cef_country_map.svg"
fig.write_image(str(fp))
