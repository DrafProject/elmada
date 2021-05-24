[![License: LGPL v3](https://img.shields.io/badge/License-LGPL%20v3-blue.svg)](https://www.gnu.org/licenses/lgpl-3.0)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

<img src="elmada_logo.svg" width="300" alt="elmada logo">

# **el**ectricity **ma**rket **da**ta for the **d**emand **r**esponse **a**nalysis **f**ramework

Elmada is part of the [Draf Project](https://github.com/DrafProject) but can be used as a standalone package. `elmada` stands for **el**ectricity **ma**rket **da**ta and allows the approximation of up to quarterhourly carbon emission factors and the provision of historic wholesale prices for European national electricity grids.

# Installation

## Conda environment with editable version of Elmada

The following code downloads the directory, creates a conda environment including all required packages, and runs all tests.

```bash
git clone https://github.com/DrafProject/elmada.git
cd elmada

# creates environment based on environment.yml and installs editable local version:
conda env create

# activate draf environment
conda activate elmada

# Run the tests and ensure that there are no errors
pytest
```

## Install only Elmada

Alternatively you can only install Elmada

```bash
python -m pip install git+https://github.com/DrafProject/elmada.git
```

# Data

Elmada caches all data in a elmada subdirectory of the default temp folder of the operating system, e.g. `%TEMP%` in Windows.

You can use Elmada in two modes which can be set with `elmada.set_mode(mode=<MODE>)`:

* `mode="live"` (default):
  * Up-to-date data are retrieved on-demand.
  * Possible years are 2015 until present.
* `mode="safe"`:
  * Data from December 2020 are used which are used in the [paper](https://doi.org/10.1016/j.apenergy.2021.117040).
  * Possible years are 2015 until 2020.

| Description | Local data location | Source | Channel |
|-|-|-|-|
| Generation time series & installed generation capacities | <temp_dir> | [ENTSO-E](https://transparency.entsoe.eu/) | 🔌 on-demand-retrieval via [EntsoePandasClient](https://github.com/EnergieID/entsoe-py#EntsoePandasClient) (requires valid [ENTSO-E API key](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html) in [elmada/api_keys](elmada/api_keys)`/entsoe.txt`) |
| Share of CCGT among gas power plants | <temp_dir> | [GEO](http://globalenergyobservatory.org/) | 🔌 on-demand-download via [Morph](https://morph.io/) (requires valid [Morph API key](https://morph.io/documentation/api) in [elmada/api_keys](elmada/api_keys)`/morph.txt`)|
| Carbon prices (EUA)| <temp_dir> | [Sandbag](https://sandbag.org.uk/carbon-price-viewer/) / [ICE](https://www.theice.com/)| 🔌 on-demand-retrieval via [Quandl](https://www.quandl.com/) (requires valid [Quandl API key](https://docs.quandl.com/docs#section-authentication) in [elmada/api_keys](elmada/api_keys)`/quandl.txt`) |
| (Average) fossil power plants sizes | <temp_dir> | [GEO](http://globalenergyobservatory.org/) | 🔌 on-demand-scraping via [BeautifulSoup4](https://pypi.org/project/beautifulsoup4/) |
| German fossil power plant list with efficiencies | <temp_dir> | [OPSD](https://open-power-system-data.org/)  | 🔌 on-demand-download from [here](https://data.open-power-system-data.org/conventional_power_plants/latest/) |
| Transmission & distribution losses | [data/worldbank](elmada/data/worldbank) | [Worldbank](https://databank.worldbank.org/reports.aspx?source=2&series=EG.ELC.LOSS.ZS) | 💾 manual download from [here](https://databank.worldbank.org/reports.aspx?source=2&series=EG.ELC.LOSS.ZS)  |
| Fuel price trends | [data/destatis](elmada/data/destatis) | [DESTATIS](https://www.destatis.de/) | 💾 manual download from [here](https://www.destatis.de/DE/Themen/Wirtschaft/Preise/Publikationen/Energiepreise/energiepreisentwicklung-xlsx-5619001.xlsx?__blob=publicationFile) |
| Fuel prices for 2015 | in code | [Konstantin.2017](https://doi.org/10.1007/978-3-662-49823-1) | 🔢 values |
| Carbon emission intensities | in code ([data/tranberg](elmada/data/tranberg)) | [Quaschning](https://www.volker-quaschning.de/datserv/CO2-spez/index_e.ph) ([Tranberg.2019](https://doi.org/10.1016/j.esr.2019.100367)) | 🔢 values |

# Citing Elmada

If you use Elmada for academic work please cite this [open access paper](https://doi.org/10.1016/j.apenergy.2021.117040).

# License

Copyright (c) 2021 Markus Fleschutz

<https://www.gnu.org/licenses/lgpl-3.0.de.html>

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
