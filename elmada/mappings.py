"""Various mappings including countries, fuel types, colors.

ISO 3166-1 alpha-2 country codes are used, see https://en.wikipedia.org/wiki/ISO_3166-1

# TODO: there is a python module for ISO 3166-1, see https://github.com/deactivated/python-iso3166

"""

import collections
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple, Union


# EU 27
EU = {
    "AT": "Austria",
    "BE": "Belgium",
    "BG": "Bulgaria",
    "CY": "Cyprus",
    "CZ": "Czech Republic",
    "DE": "Germany",
    "DK": "Denmark",
    "EE": "Estonia",
    "ES": "Spain",
    "FI": "Finland",
    "FR": "France",
    "GR": "Greece",
    "HR": "Croatia",
    "HU": "Hungary",
    "IE": "Ireland",
    "IT": "Italy",
    "LT": "Lithuania",
    "LU": "Luxembourg",
    "LV": "Latvia",
    "MT": "Malta",
    "NL": "Netherlands",
    "PL": "Poland",
    "PT": "Portugal",
    "RO": "Romania",
    "SE": "Sweden",
    "SI": "Slovenia",
    "SK": "Slovakia",
}

# Non-EU27 European countries
OTHER = {
    "AD": "Andorra",
    "AL": "Albania",
    "AM": "Armenia",
    "AZ": "Azerbaijan",
    "BA": "Bosnia and Herzegovina",
    "BY": "Belarus",
    "CH": "Switzerland",
    "FO": "Faeroe Islands",
    "GB": "United Kingdom",
    "GE": "Georgia",
    "GI": "Gibraltar",
    "IS": "Iceland",
    "KZ": "Kazakhstan",
    "LI": "Liechtenstein",
    "MC": "Monaco",
    "MD": "Moldova",
    "ME": "Montenegro",
    "MK": "Macedonia",
    "NO": "Norway",
    "RS": "Serbia",
    "RU": "Russian Federation",
    "SM": "San Marino",
    "TR": "Turkey",
    "UA": "Ukraine",
    "VA": "Vatican City State",
    "XK": "Kosovo",
}

# Countries that are excluded form the analysis
EXCLUDED = {
    "AD": "No generation data available from ENTSO-E",
    "AM": "No generation data available from ENTSO-E",
    "AZ": "No generation data available from ENTSO-E",
    "CY": "No generation data available from ENTSO-E",
    "FO": "No generation data available from ENTSO-E",
    "GE": "No generation data available from ENTSO-E",
    "GI": "No generation data available from ENTSO-E",
    "IS": "No generation data available from ENTSO-E",
    "KZ": "No generation data available from ENTSO-E",
    "LI": "No generation data available from ENTSO-E",
    "MC": "No generation data available from ENTSO-E",
    "MD": "No generation data available from ENTSO-E",
    "SM": "No generation data available from ENTSO-E",
    "VA": "No generation data available from ENTSO-E",
    "XK": "No generation data available from ENTSO-E",
    "LU": "No generation data available from ENTSO-E",
    "RU": "No generation data available from ENTSO-E",
    "TR": "No generation data available from ENTSO-E",
    "MT": "No generation data available from ENTSO-E",
    "HR": "No generation data available from ENTSO-E",
    "UA": "No generation data available from ENTSO-E",
    "AL": "No generation data available from ENTSO-E",
    "BY": "No generation data available from ENTSO-E",
    "BA": "Only coal as conventional generation data from ENTSO-E.",
    "CH": "Only nuclear as conventional generation data from ENTSO-E.",
    "SE": "Only nuclear as conventional generation data from ENTSO-E.",
    "NO": "Only gas as conventional generation data from ENTSO-E.",
    "LV": "Only gas as conventional generation data from ENTSO-E.",
    "MK": "Only lignite as conventional generation data from ENTSO-E.",
    "ME": "Only lignite as conventional generation data from ENTSO-E.",
    "EE": "Only other_conv as conventional generation data from ENTSO-E.",
    # "LT": "Only gas & oil as conventional generation data from ENTSO-E.",
    "BG": "No installed capacity for 2019 from ENTSO-E",
    "SK": "No installed capacity for 2019 from ENTSO-E",
}

EUROPE_COUNTRIES = {**EU, **OTHER}

EUROPE_COUNTRIES_LONG_TO_SHORT = {long: short for short, long in EUROPE_COUNTRIES.items()}

d = {k: v for k, v in EUROPE_COUNTRIES.items() if k not in EXCLUDED}
COUNTRIES_FOR_ANALYSIS = collections.OrderedDict(sorted(d.items()))

# Modified entsoe-py mapping to match whole countries
NEIGHBOURS_CY = {
    "AT": ["CH", "CZ", "DE", "HU", "IT", "SI"],
    "BA": ["HR", "ME", "RS"],
    "BE": ["NL", "DE", "FR", "GB"],
    "BG": ["GR", "MK", "RO", "RS", "TR"],
    "CH": ["AT", "DE", "FR", "IT"],
    "CZ": ["AT", "DE", "PL", "SK"],
    "DE": ["AT", "BE", "CH", "CZ", "DK", "FR", "IT", "NL", "PL", "SE", "SI"],
    "DK": ["DE", "NO", "SE"],
    "EE": ["FI", "LV", "RU"],
    "ES": ["FR", "PT"],
    "FI": ["EE", "NO", "RU", "SE", "SE"],
    "FR": ["BE", "CH", "DE", "ES", "GB", "IT"],
    "GB": ["BE", "FR", "IE", "NL"],
    "GR": ["AL", "BG", "IT", "MK", "TR"],
    "HU": ["AT", "HR", "RO", "RS", "SK", "UA"],
    "IE": ["GB"],
    "IT": ["AT", "FR", "DE", "GR", "MT", "ME", "SI", "CH"],
    "LT": ["BY", "LV", "PL", "RU", "SE"],
    "LV": ["EE", "LT", "RU"],
    "ME": ["AL", "BA", "RS"],
    "MK": ["BG", "GR", "RS"],
    "MT": ["IT"],
    "NL": ["BE", "DE", "DE", "GB", "NO"],
    "NO": ["SE", "FI", "DK", "NL"],
    "PL": ["CZ", "DE", "DE", "LT", "SE", "SK", "UA"],
    "PT": ["ES"],
    "RO": ["BG", "HU", "RS", "UA"],
    "RS": ["AL", "BA", "BG", "HR", "HU", "ME", "MK", "RO"],
    "SE": ["FI", "NO", "DE", "DK", "LT", "PL"],
    "SI": ["AT", "DE", "HR", "IT"],
    "SK": ["CZ", "HU", "PL", "UA"],
}


EU_de_for_gas_price = {
    "AT": "Österreich",
    "BE": "Belgien",
    "BG": "Bulgarien",
    "CZ": "Tschechiensche\nRepublik",
    "DE": "Deutschland",
    "DK": "Dänemark",
    "EE": "Estland",
    "ES": "Spanien",
    "FI": "Finnland",
    "FR": "Frankreich",
    "GB": "Vereinigtes\nKönigreich",
    "GE": "Georgien",
    "GR": "Griechenland",
    "HR": "Kroatien",
    "HU": "Ungarn",
    "IE": "Irland",
    "IT": "Italien",
    "LT": "Litauen",
    "LU": "Luxemburg",
    "LV": "Lettland",
    "MK": "Mazedonien",
    "NL": "Niederlande",
    "PO": "Polen",
    "PT": "Portugal",
    "RO": "Rumänien",
    "SE": "Schweden",
    "SI": "Slowenien",
    "SK": "Slowakei",
    "TR": "Türkei",
    "UA": "Ukraine",
}

TECH_COLORS = {
    "load": "grey",
    "biomass": "olive",
    "hydro": "lightseagreen",
    "solar": "gold",
    "wind_onshore": "royalblue",
    "wind_offshore": "navy",
    "other_RES": "lightgreen",
    "nuclear": "deeppink",
    "lignite": "chocolate",
    "coal": "saddlebrown",
    "pumped_hydro": "mediumseagreen",
    "gas": "darkgreen",
    "gas_cc": "lightgreen",
    "oil": "darkgrey",
    "other_conv": "lightgray",
    "nan": "red",
}

ORDERED_ENTSOE_FUELS = [
    "Solar",
    "Wind Offshore",
    "Wind Onshore",
    "Other renewable",
    "Geothermal",
    "Waste",
    "Biomass",
    "Hydro Run-of-river and poundage",
    "Hydro Water Reservoir",
    "Marine",
    "Nuclear",
    "Fossil Brown coal/Lignite",
    "Fossil Hard coal",
    "Fossil Gas",
    "Fossil Oil",
    "Other_conventional",
    "Other",
    "Fossil Oil shale",
    "Fossil Coal-derived gas",
    "Fossil Peat",
    "Hydro Pumped Storage",
]


FUEL_AGGREGATION = {
    "Other": "other_conv",
    "other_conventional": "other_conv",
    "Fossil Coal-derived gas": "other_conv",
    "Fossil Oil shale": "other_conv",
    "Fossil Peat": "other_conv",
    "Waste": "other_RES",
    "Geothermal": "other_RES",
    "Hydro Water Reservoir": "other_RES",
    "Marine": "other_RES",
    "Other renewable": "other_RES",
    "other renewables": "other_RES",
}

FUEL_RENAME = {
    "Biomass": "biomass",
    "Fossil Brown coal/Lignite": "lignite",
    "Fossil Oil": "oil",
    "Fossil Gas": "gas",
    "Fossil Hard coal": "coal",
    "Hydro Pumped Storage": "pumped_hydro",
    "Hydro Run-of-river and poundage": "hydro",
    "Nuclear": "nuclear",
    "Solar": "solar",
    "Wind Offshore": "wind_offshore",
    "Wind Onshore": "wind_onshore",
}

OPSD_TO_DRAF = {
    "Hard coal": "coal",
    "Lignite": "lignite",
    "Natural gas": "gas",
    "Nuclear": "nuclear",
    "Oil": "oil",
}

# Fuels after aggregation
RES = ["hydro", "biomass", "solar", "wind_offshore", "wind_onshore", "other_RES"]
CONV = ["nuclear", "lignite", "coal", "pumped_hydro", "gas", "oil", "other_conv"]
DRAF_FUELS = RES + CONV

# Fuels for calculation of residual load (simplified merit order simulation)
CONV2 = ["nuclear", "lignite", "coal", "gas", "oil"]
RES2 = [f for f in DRAF_FUELS if f not in CONV2]

# Fuels for simplified merit oder simulation
PWL_FUELS = ["nuclear", "lignite", "coal", "gas_cc", "gas", "oil"]


def get_tech_colors(technologies: Iterable[str]) -> List[str]:
    """Returns list of colours for given list of technologies."""
    return [TECH_COLORS[i] for i in technologies]
