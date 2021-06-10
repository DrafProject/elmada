<img src="elmada_logo.svg" width="450" alt="elmada logo">

# Electricity market data for energy system modeling

[![License: LGPL v3](https://img.shields.io/badge/License-LGPL%20v3-blue.svg)](https://www.gnu.org/licenses/lgpl-3.0)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Elmada stands for **el**ectricity **ma**rket **da**ta and provides carbon emission factors as well as whole sale prices for energy system modeling with focus on the demand side, e.g., demand response potential analyses.

Elmada uses historic electricity generation data to calculate carbon emission factors for European countries.
Based on the methodology described in [this open access paper](https://doi.org/10.1016/j.apenergy.2021.117040), grid mix emission factors (XEFs) and marginal emission factors (MEF) are calculated in up to quarter-hourly resolution.

As a side product, historic wholesale prices and fuel-specific generation for European national electricity grids can be provided.
Elmada is part of the [Draf Project](https://github.com/DrafProject) (Demand Response Analysis Framework) but can be used as a standalone package.

# Installation

## Conda environment with editable version of Elmada

The following code downloads the directory, creates a Conda environment including all required packages, and runs all tests.

```bash
git clone https://github.com/DrafProject/elmada.git
cd elmada

# creates environment based on environment.yml and installs an editable local Elmada version
conda env create

# activate draf environment
conda activate elmada

# Run the tests and ensure that there are no errors
pytest
```

## Install only Elmada

Alternatively, you can install only the Elmada module including the data:

```bash
python -m pip install git+https://github.com/DrafProject/elmada.git
```

# Usage

```python
import elmada

elmada.get_emissions(year=2019, country="DE", method="MEF_PWL")
```


# Data

You can use Elmada in two modes which can be set with `elmada.set_mode(mode=<MODE>)`:

* `mode="safe"` (default):
  * Pre-cached data for 4 years and 20 countries are used. The data are described in the [paper](https://doi.org/10.1016/j.apenergy.2021.117040).
  * The years are 2017 to 2020 and the countries AT, BE, CZ, DE, DK, ES, FI, FR, GB, GR, HU, IE, IT, LT, NL, PL, PT, RO, RS, SI.
  * The data is available in the space-saving and quick-to-read [Parquet format](https://parquet.apache.org/) under [data/safe_cache](elmada/data/safe_cache).
* `mode="live"`:
  * Up-to-date data are retrieved on demand and are cached to an OS-specific directory, see `elmada.paths.CACHE_DIR`. A symbolic link to it can be conveniently created by executing `elmada.helper.make_symlink_to_cache()`.
  * Available years are 2017 until present.
  * Slow due to several API requests.
  * Requires valid API keys of Entsoe, Morph, Quandl, see table below.

| Description | Local data location | Source | Channel |
|-|-|-|-|
| Generation time series & installed generation capacities | <temp_dir> | [ENTSO-E](https://transparency.entsoe.eu/) | 🔌 on-demand-retrieval via [EntsoePandasClient](https://github.com/EnergieID/entsoe-py#EntsoePandasClient) (requires valid [ENTSO-E API key](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html) in [elmada/api_keys](elmada/api_keys)`/entsoe.txt`) |
| Share of CCGT among gas power plants | <temp_dir> | [GEO](http://globalenergyobservatory.org/) | 🔌 on-demand-download via [Morph](https://morph.io/) (requires valid [Morph API key](https://morph.io/documentation/api) in [elmada/api_keys](elmada/api_keys)`/morph.txt`)|
| Carbon prices (EUA)| <temp_dir> | [Sandbag](https://sandbag.org.uk/carbon-price-viewer/) / [ICE](https://www.theice.com/)| 🔌 on-demand-retrieval via [Quandl](https://www.quandl.com/) (requires valid [Quandl API key](https://docs.quandl.com/docs#section-authentication) in [elmada/api_keys](elmada/api_keys)`/quandl.txt`) |
| (Average) fossil power plants sizes | <temp_dir> | [GEO](http://globalenergyobservatory.org/) | 🔌 on-demand-scraping via [BeautifulSoup4](https://pypi.org/project/beautifulsoup4/) |
| German fossil power plant list with efficiencies | <temp_dir> | [OPSD](https://open-power-system-data.org/)  | 🔌 on-demand-download from [here](https://data.open-power-system-data.org/conventional_power_plants/latest/) |
| Transmission & distribution losses | [.../worldbank](elmada/data/raw/worldbank) | [Worldbank](https://databank.worldbank.org/reports.aspx?source=2&series=EG.ELC.LOSS.ZS) | 💾 manual download from [here](https://databank.worldbank.org/reports.aspx?source=2&series=EG.ELC.LOSS.ZS)  |
| Fuel price trends | [.../destatis](elmada/data/raw/destatis) | [DESTATIS](https://www.destatis.de/) | 💾 manual download from [here](https://www.destatis.de/DE/Themen/Wirtschaft/Preise/Publikationen/Energiepreise/energiepreisentwicklung-xlsx-5619001.xlsx?__blob=publicationFile) |
| Fuel prices for 2015 | in code | [Konstantin.2017](https://doi.org/10.1007/978-3-662-49823-1) | 🔢 hard-coded values |
| Carbon emission intensities | in code ([.../tranberg](elmada/data/raw/tranberg)) | [Quaschning](https://www.volker-quaschning.de/datserv/CO2-spez/index_e.ph) ([Tranberg.2019](https://doi.org/10.1016/j.esr.2019.100367)) | 🔢 hard-coded values |

# Citing Elmada

If you use Elmada for academic work please consider citing [this open access paper](https://doi.org/10.1016/j.apenergy.2021.117040) published in Applied Energy in 2021.

# License

Copyright (c) 2021 Markus Fleschutz

[![License: LGPL v3](https://img.shields.io/badge/License-LGPL%20v3-blue.svg)](https://www.gnu.org/licenses/lgpl-3.0)

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
