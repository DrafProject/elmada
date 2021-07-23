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
To properly assess this flexibility within energy system models, it is essential to know the wholesale price and associated carbon emissions per unit of electricity for a given time step.

`elmada` is an easy-to-use open-source Python package designed to provide dynamic electricity carbon emission factors and prices for European countries.
The target group includes modelers of distributed energy hubs who need electricity market data. This is where the name **elmada** comes from: **el**ectricity **ma**rket **da**ta.
`elmada` is developed in the open on GitHub [@ElmadaGitHub] and each release is archived on Zenodo [@ElmadaZenodo].
To the best of the authors' knowledge, `elmada` is the first free and open-source Python interface for dynamic emission factors in Europe.
This makes `elmada` an important complement to existing commercial services, such as the electricityMap API [@ElecMapApi] and the Automated Emissions Reduction from WattTime [@WattTime].

Currently, `elmada` provides data for 20 European countries and for each year since 2017.
`elmada` works mainly with data from the ENTSO-E Transparency Platform [@ENTSOE].

Two types of carbon emission factors are calculated:

* grid-mix emission factors (XEFs), which represent the emission intensity based on the current generation mix of the electricity system,
* and marginal emission factors (MEFs), which quantify the emission intensity of the generators likely to react to a marginal system change.

MEFs are more challenging to approximate than XEFs since MEFs require the identification of the marginal power plants per time step.
In `elmada`, this is done through a merit order simulation within the PP and PWL method described in [@Fleschutz2021].

So far, `elmada` has been used in a study where MEFs, XEFs and the results of load shift simulations based on them are compared across 20 European countries [@Fleschutz2021].
In ongoing research, `elmada` is used to quantify the costs and emission-saving potentials that arise from the exploitation of existing and future flexibility in decentral energy hubs.

We hope that `elmada` reduces the difficulty associated with the use of dynamic carbon emission factors and prices in the modeling of decentral energy systems.

# Acknowledgements

The author acknowledges funding by the MTU Risam scholarship scheme and the German Federal Ministry of the Environment, Nature Conservation and Nuclear Safety (BMU) via the project WIN4Climate (No. 03KF0094 A) as part of the National Climate Initiative.

# References
