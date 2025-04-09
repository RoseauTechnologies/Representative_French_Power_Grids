# Representative networks of France's electricity distribution network

This GitHub repository provides the 150 MV feeders with all underlying LV networks used in [Seddik Yassine
Abdelouadoud's study](https://www.data.gouv.fr/fr/datasets/departs-hta-representatifs-pour-lanalyse-des-reseaux-de-distribution-francais/).
These networks were selected from among French distribution networks as being representative of it. The details of
the procedure used to select them are available in a report accessible via the previous link (French only).

In this repository, an updated version of the files representing these networks is available for direct use with
[_Roseau Load Flow_](https://github.com/RoseauTechnologies/Roseau_Load_Flow).

![Map of the networks](Map.jpeg)

## Setup

In order to start using these networks, `roseau-load-flow>=0.12.0` must be installed. It can be achieved via `uv`:

```bash
# Install a virtual environment (optional)
uv python pin 3.13
uv venv

# Use the `pyproject.toml` and `uv.lock` files provided in this repository
uv sync
```

or via `pip`:

```bash
# In your virtual environment
pip install roseau-load-flow>=0.12.0
```

For more information, see the "Installation" page of the _Roseau Load Flow_ documentation available
[here](https://roseau-load-flow.roseautechnologies.com/en/stable/Installation.html).

## Usage

The networks can be used directly in the following way:

```python
import roseau.load_flow as rlf

# Read a network from this repository
en = rlf.ElectricalNetwork.from_json("./data/networks/11_MVFeeder0725.json")
# <ElectricalNetwork: 336 buses, 324 lines, 10 transformers, 1 switch, 626 loads, 1 source, 1 ground, 1 potential ref, 11 ground connections>

# Solve a load flow
# The environment variable "ROSEAU_LOAD_FLOW_LICENSE_KEY" must be defined in your environment
en.solve_load_flow()
# (3, 2.1200179389779805e-09)

# Access the results
# By instance, voltages as data frame
en.res_buses_voltages
#                                            voltage  ...  nominal_voltage
# bus_id           phase                              ...
# MVVoltage_source an     11777.945491+    0.000000j  ...              NaN
#                  bn     -5888.972746-10200.000000j  ...              NaN
#                  cn     -5888.972746+10200.000000j  ...              NaN
# 11_BUZEN         ab     17666.918237+10200.000000j  ...          20000.0
#                  bc         0.000000-20400.000000j  ...          20000.0
# ...                                            ...  ...              ...
# 11_LVBus0536527  bn        -4.022833-  230.169477j  ...            400.0
#                  cn      -196.023130+  119.090298j  ...            400.0
# 11_LVBus0536528  an       202.935062+  115.256587j  ...            400.0
#                  bn        -4.011705-  230.092439j  ...            400.0
#                  cn      -195.982822+  119.122054j  ...            400.0
# [1008 rows x 6 columns]
```

For more information about the license key for _Roseau Load Flow_, please visit
[this page](https://roseau-load-flow.roseautechnologies.com/en/stable/License.html).

The name of the networks' files can be read as follows: for instance, with `11_MVFeeder0725.json`:

- `11` is the code of the French region the network is located (see below);
- `MVFeeder0725` is the (internal) name that was given to this MV feeder.

The regional codes are as follows. Only French metropolitan regions were considered in this study.

| Code | Name                       |
| :--- | :------------------------- |
| 11   | Île-de-France              |
| 24   | Centre-Val de Loire        |
| 27   | Bourgogne-Franche-Comté    |
| 28   | Normandie                  |
| 32   | Hauts-de-France            |
| 44   | Grand Est                  |
| 52   | Pays de la Loire           |
| 53   | Bretagne                   |
| 75   | Nouvelle-Aquitaine         |
| 76   | Occitanie                  |
| 84   | Auvergne-Rhône-Alpes       |
| 93   | Provence-Alpes-Côte d'Azur |

See this [Wikipedia page](https://www.wikiwand.com/en/articles/Regions_of_France#List_of_administrative_regions) for
more information.

## Extrapolating the results

This study also provides a size for each cluster, indicating its representativeness within France. These sizes are stored in the file `./data/Cluster_Size.csv`.

For example, the representativeness size of the network `11_MVFeeder0725` is 326.

| network_id          | cluster_size |
| :------------------ | :----------- |
| **11_MVFeeder0725** | **326**      |
| 11_MVFeeder1363     | 258          |
| 11_MVFeeder1365     | 408          |
| 11_MVFeeder2143     | 232          |
| 11_MVFeeder2298     | 151          |
| ...                 | ...          |

The total cluster size is 24135, so the network `11_MVFeeder0725` represents 1.3507% of the French distribution network.

The following section is a translation of the dataset description made available by Mr. Abdelouadoud on the
[data.gouv.fr](https://www.data.gouv.fr/fr/datasets/departs-hta-representatifs-pour-lanalyse-des-reseaux-de-distribution-francais/)
website.

## Scripts

The `scripts/` folder contains two scripts:

- `convert_networks.py`: Downloads network files in their original format and converts them to the latest _Roseau
  Load Flow_ JSON format.
- `plot_networks.py`: Plots the networks using the folium library and generates regional maps showing all networks
  within each region.

To run these scripts:

```bash
uv run scripts/convert_networks.py
uv run scripts/plot_networks.py
```

## Representative MV Feeders for the Analysis of French Distribution Networks

### Description

This dataset provides a selection of representative medium-voltage (MV) feeders from French distribution networks.
Designed to facilitate planning and operational studies of electrical networks, it is a key resource for researchers,
engineers, and decision-makers.

### Dataset Content

- MV and LV Feeder Traces: Line geometries, including location and typology information (overhead or underground).
- Technical Characteristics: Conductor section and type per line, rated power of MV/LV transformers.
- Consumption: Examples of consumption drawn per node and per phase.

### Constitution Methodology

This dataset was developed from open data from reliable sources, such as network traces published by the ORE agency,
local energy consumption data, and building geometries provided by the
[_Institut Géographique National_](https://www.ign.fr/) (IGN i.e. _National Geographic Institute_)
([BDTOPO](https://geoservices.ign.fr/bdtopo)). The feeders were selected using
advanced clustering algorithms, ensuring a balanced distribution of representative cases across the French territory.

### Use Cases

- Network Planning: Assessment of hosting capacities and anticipation of local constraints.
- Energy Studies: Simulation of scenarios for the deployment of renewable energies and electrification.
- Academic Research: Development and testing of new electrical network modeling methods.

### License and Access

The dataset is made available under the Open License version 2.0, promoting its use, reuse, and sharing. You can
download the files and access the full documentation via
[this page](https://www.data.gouv.fr/fr/datasets/departs-hta-representatifs-pour-lanalyse-des-reseaux-de-distribution-francais/).

For a comprehensive report describing the
methodology: [Methodological Report](https://storage.googleapis.com/roseau-post-doc-report/selection%20departs%20HTA%20representatifs.pdf)

Contribute to the future of electrical networks by exploring and utilizing this unique dataset in France!
