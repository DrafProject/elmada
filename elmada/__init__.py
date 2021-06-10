from elmada._version import __version__

from .mode import get_mode, set_mode

from . import (
    from_entsoe,
    eu_pwl,
    from_geo_via_morph,
    from_opsd,
    from_other,
    cc_share,
    from_smard,
    from_geo_scraped,
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
