__title__ = "elmada"
__summary__ = "Dynamic electricity carbon emission factors and prices for Europe"
__uri__ = "https://github.com/DrafProject/elmada"

__version__ = "0.0.6"

__author__ = "Markus Fleschutz"
__email__ = "mfleschutz@gmail.com"

__license__ = "LGPLv3"
__copyright__ = f"Copyright (C) 2021 {__author__}"

# isort: off

from .mode import get_mode, set_mode
from .helper import set_api_keys, make_symlink_to_cache

# isort: on

from . import (
    cc_share,
    eu_pwl,
    from_entsoe,
    from_geo_scraped,
    from_geo_via_morph,
    from_opsd,
    from_other,
    from_smard,
    helper,
    paths,
    plots,
)
from .main import (
    get_el_national_generation,
    get_emissions,
    get_merit_order,
    get_prices,
    get_residual_load,
)
