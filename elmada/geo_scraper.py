import pandas as pd
import requests
from bs4 import BeautifulSoup
from IPython.display import display

from elmada import helper as hp
from elmada import mappings as mp
from elmada import el_geo_morph as gm
from elmada import paths


def get_pp_sizes_for_pwl() -> pd.DataFrame:
    df = get_pp_sizes()
    df = df.fillna(df.mean()).astype(int)
    return df


def get_pp_sizes() -> pd.DataFrame:
    geo = get_units_of_geo_list()

    grouper = geo.groupby(["cy", "fuel"])["capa"]
    pp_sizes = grouper.mean().unstack()
    count = grouper.count().unstack()
    pp_sizes = pp_sizes.where(count >= 2)
    return pp_sizes[mp.PWL_FUELS]


def get_units_of_geo_list(cache: bool = True) -> pd.DataFrame:
    fp = paths.CACHE_DIR / "units_of_geo_list.h5"

    if fp.exists() and cache:
        df = pd.read_hdf(fp)

    else:
        geo = gm.get_geo_list()
        max_count = len(geo)
        print(f"Download {max_count} items:", end="")
        concat_list = []

        for _, ser in geo.iterrows():
            print(".", end="")
            geo_id = ser["id"]
            print(geo_id, end=", ")
            df = get_df_from_geo_id(geo_id)
            df["cy"] = ser["cy"]
            df["fuel"] = ser["fuel"]
            df["geoid"] = geo_id
            concat_list.append(df)

        df = pd.concat(concat_list)
        hp.write_array(df, fp)

    df = df.rename(
        columns={
            "Capacity (MWe)": "capa",
            "Unit Efficiency (%)": "eff",
            "Date Commissioned (yyyy-mm-dd)": "commissioned",
            "Unit #": "unit_no",
        },
    )

    interesting_cols = ["cy", "fuel", "geoid", "capa", "eff", "commissioned", "unit_no"]
    df = df.loc[df.capa != "", interesting_cols]

    df["capa"] = df["capa"].astype(float).astype(int)
    return df.reset_index(drop=True)


def get_df_from_geo_id(geo_id: int) -> pd.DataFrame:
    url = f"http://globalenergyobservatory.org/geoid/{geo_id}"
    page = requests.get(url).text
    soup = BeautifulSoup(page, "lxml")
    selector = soup.find("div", {"id": "UnitDescription_Block"})

    table = selector.find("table")

    headers = [cell.get_text().strip() for cell in table.findAll("th")]
    ncols = len(headers)
    rows = table.findAll("tr")

    df = pd.DataFrame(columns=headers)
    for i, row in enumerate(rows):
        cells = row.find_all("td")
        if len(cells) == ncols:
            df.loc[i, :] = [cell.find("input").get("value") for cell in cells]
    return df
