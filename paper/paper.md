---
title: 'elmada: Dynamic electricity carbon emission factors and prices for Europe'
tags:
  - energy
  - electricity market
  - carbon emissions
  - marginal emissions
  - python
authors:
 - name: Markus Fleschutz
   orcid: 0000-0002-8516-9635
   affiliation: 1, 2
 - name: Michael D. Murphy
   orcid: 0000-0002-4269-2581
   affiliation: 1
affiliations:
 - name: Department of Process, Energy and Transport Engineering, Munster Technological University
   index: 1
 - name: Institute of Refrigeration, Air-Conditioning, and Environmental Engineering, Karlsruhe University of Applied Sciences
   index: 2
date: 23 July 2021
bibliography: paper.bib
---

# Summary

The expansion of intermittent renewable energy sources such as solar and wind requires increased operational flexibility in electricity systems.
Energy system models at the scale of individual decentral energy hubs can help decision-makers of energy hubs such as city quarters or industrial sites evaluate the cost and carbon emission saving potentials of their flexibility.
For national scale models, the carbon emissions of the electricity supply system are endogenously determined.
However, low-level models (at the scale of decentral energy hubs) need this information as input.
And since specific carbon emissions of national electricity supply systems fluctuate hourly, the usage of at least hourly resolved carbon emission factors (CEFs) is essential [@Prina2020].

`elmada` is an easy-to-use open-source Python package designed to provide dynamic electricity CEFs and prices for European countries.
The target group includes modelers of distributed energy hubs who need electricity market data.
This is where the name **elmada** comes from: **el**ectricity **ma**rket **da**ta.
`elmada` is developed in the open on GitHub [@ElmadaGitHub] and each release is archived on Zenodo [@ElmadaZenodo].

# Statement of Need

Dynamic CEFs are important for the environmental assessment of electricity supply in not fully decarbonized energy systems.
To the best of the authors' knowledge, `elmada` is the first free and open-source Python interface for dynamic CEFs in Europe.
This makes `elmada` an important complement to existing commercial services.

At the moment, there are two main commercial services that provide an Application Programming Interface (API) for historical dynamic CEFs: the `electricityMap` API [@ElecMapApi] and the Automated Emissions Reduction from WattTime [@WattTime].
The `electricityMap` is maintained by Tomorrow, a startup based in Denmark, and WattTime is a nonprofit organization in the USA.
However, both focus on real-time CEFs as incentive signals for demand response answering the question "How clean is my electricity right now?".
We elaborate more on `electricityMap` here, as they originate in Europe, which is also the focus of `elmada`.
The services of WattTime are broadly similar.

`electricityMap` is a software project that visualizes the carbon emission intensity linked to the generation and consumption of electricity on a global choropleth map.
Additionally, the `electricityMap` API provides historical, real-time (current hour), forecast, and since recently also marginal data. The calculation methods consider international energy exchanges and the fact that the list of data sources is curated by Tomorrow (the company behind it) makes it save-to-use as a live incentive signal e.g. for carbon-based demand response applications.
However, the use of `electricityMap` API requires a data-dependent payment even for the historic data, so it is not free of charge.

Currently, there is no multi-national solution for modelers of decentral energy hubs searching for free historical hourly CEFs (in particular MEFs).
This gap often leads to the usage of yearly average CEFs, which are potentially misleading [@Hawkes2010].
We close this gap by providing the conveniently installable Python package `elmada` that calculates XEFs and MEFs in hourly (or higher) resolution for 30 European countries for free.
`elmada` provides modelers a no-regret (free) entry point to European dynamic CEFs leaving it open to the modeler to later switch to a paid service that generate more accurate CEFs, e.g. through advanced methods such as the consideration of cross-border energy flows through flow tracing [@Tranberg2019].

# Functionality

Two types of CEFs are calculated:

* grid-mix emission factors (XEFs), which represent the emission intensity based on the current generation mix of the electricity system,
* and marginal emission factors (MEFs), which quantify the emission intensity of the generators likely to react to a marginal system change.

MEFs are more challenging to approximate than XEFs since MEFs require the identification of the marginal power plants per time step.
In `elmada`, this is done through a merit order simulation within the PP and PWL method described in [@Fleschutz2021].

Also, historical and simulated day-ahead electricity market prices are provided.
They can be used either for the economic evaluation of electricity demands or to model the incentive signal of price-based demand response.

Currently, `elmada` provides data for 30 European countries and for each year since 2017.
`elmada` works mainly with data from the ENTSO-E Transparency Platform [@ENTSOE].

# Current and Future Usage

So far, `elmada` has been used in a study where MEFs, XEFs and the results of load shift simulations based on them are compared across 20 European countries [@Fleschutz2021].
In ongoing research, `elmada` is used to quantify the costs and emission-saving potentials that arise from the exploitation of existing and future flexibility in decentral energy hubs.

We hope that `elmada` reduces the difficulty associated with the use of dynamic CEFs and prices in the modeling of decentral energy systems.

# Acknowledgements

The author acknowledges funding by the MTU Risam scholarship scheme and the German Federal Ministry of the Environment, Nature Conservation and Nuclear Safety (BMU) via the project WIN4Climate (No. 03KF0094 A) as part of the National Climate Initiative.

# References
