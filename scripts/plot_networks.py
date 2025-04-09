"""
This script plots the networks using the folium library and generates regional maps showing all networks within each
region.
"""

# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "folium>=0.19.5",
#     "pandas>=2.2.3",
#     "rich>=14.0.0",
#     "roseau-load-flow>=0.12.0",
# ]
# ///

import logging
import re
import unicodedata
from pathlib import Path

import folium
import pandas as pd
import roseau.load_flow as rlf
from branca.element import Element, Figure
from jinja2 import Template
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn

logger = logging.getLogger(__name__)

HV_MV_SUBSTATION_ID_PATTERN: re.Pattern[str] = re.compile(r"^[0-9]{2}_[A-Z]+[0-9]?$")
MV_LV_SUBSTATION_ID_PATTERN: re.Pattern[str] = re.compile(r"^[0-9]{2}_MVLV[0-9]+$")
MV_BUS_ID_PATTERN: re.Pattern[str] = re.compile(r"^[0-9]{2}_MVBus[0-9]+$")
# LV_BUS_ID_PATTERN: re.Pattern[str] = re.compile(r"^[0-9]{2}_LVBus[0-9]+$")
# MV_LINE_ID_PATTERN: re.Pattern[str] = re.compile(r"^[0-9]{2}_MVBranch[0-9]+$")
LV_LINE_ID_PATTERN: re.Pattern[str] = re.compile(r"^[0-9]{2}_LVBranch[0-9]+$")
FRENCH_REGIONS_CODES = {
    11: "Île-de-France",
    24: "Centre-Val de Loire",
    27: "Bourgogne-Franche-Comté",
    28: "Normandie",
    32: "Hauts-de-France",
    44: "Grand Est",
    52: "Pays de la Loire",
    53: "Bretagne",
    75: "Nouvelle-Aquitaine",
    76: "Occitanie",
    84: "Auvergne-Rhône-Alpes",
    93: "Provence-Alpes-Côte d'Azur",
}


def buses_style_function(feature):
    bus_id = feature["properties"]["id"]
    if HV_MV_SUBSTATION_ID_PATTERN.fullmatch(bus_id):  # HV/MV substation
        return {
            "fill": True,
            "fillColor": "#000000",
            "color": "#000000",
            "fillOpacity": 1,
            "radius": 7,
        }
    elif MV_LV_SUBSTATION_ID_PATTERN.fullmatch(bus_id):  # MV/LV substations
        return {
            "fill": True,
            "fillColor": "#234e83",
            "color": "#234e83",
            "fillOpacity": 1,
            "radius": 5,
        }
    elif MV_BUS_ID_PATTERN.fullmatch(bus_id):  # MV buses
        return {
            "fill": True,
            "fillColor": "#234e83",
            "color": "#234e83",
            "fillOpacity": 1,
            "radius": 3,
        }
    else:  # LV buses
        return {
            "fill": True,
            "fillColor": "#adb9cb",
            "color": "#adb9cb",
            "fillOpacity": 1,
            "radius": 1,
        }


def buses_highlight_function(feature):
    return {"color": "#cad40e", "fillColor": "#cad40e"}


buses_tooltip = folium.GeoJsonTooltip(
    fields=["id", "phases"],
    aliases=["Id:", "Phases:"],
    localize=True,
    sticky=False,
    labels=True,
    max_width=800,
)

buses_tooltip_with_network = folium.GeoJsonTooltip(
    fields=["id", "phases", "network"],
    aliases=["Id:", "Phases:", "Network:"],
    localize=True,
    sticky=False,
    labels=True,
    max_width=800,
)


def lines_style_function(feature):
    line_id = feature["properties"]["id"]
    if LV_LINE_ID_PATTERN.fullmatch(line_id):
        return {"color": "#adb9cb", "weight": 3}
    else:
        return {"color": "#234e83", "weight": 4}


def lines_highlight_function(feature):
    return {"color": "#cad40e"}


lines_tooltip = folium.GeoJsonTooltip(
    fields=["id", "phases", "bus1_id", "bus2_id", "parameters_id", "length"],
    aliases=["Id:", "Phases:", "Bus1:", "Bus2:", "Parameters:", "Length (km):"],
    localize=True,
    sticky=False,
    labels=True,
    max_width=800,
)

lines_tooltip_with_network = folium.GeoJsonTooltip(
    fields=["id", "phases", "bus1_id", "bus2_id", "parameters_id", "length", "network"],
    aliases=["Id:", "Phases:", "Bus1:", "Bus2:", "Parameters:", "Length (km):", "Network:"],
    localize=True,
    sticky=False,
    labels=True,
    max_width=800,
)


class RoseauMap(folium.Map):
    def render(self, title: str | None, **kwargs) -> None:
        """Add the network name to the function signature.

        Args:
            title:
                The pretty version of the network name.

        Keyword Args:
            Traditional render arguments
        """
        figure = self.get_root()
        assert isinstance(figure, Figure), "You cannot render this Element if it is not in a Figure."

        # Add a title to the figure
        figure.title = title

        # Add description and keywords in the headers
        figure.header.add_child(
            Element(
                '<meta content="The Roseau Load Flow solver can be used to interact with 150 representative French '
                'distribution networks." lang="en" name="description" xml:lang="en"/>'
            ),
            name="meta_description",
        )
        figure.header.add_child(
            Element(
                '<meta content="distribution grid, network data, lv network, mv network, free" lang="en" '
                'name="keywords" xml:lang="en"/>'
            ),
            name="meta_keywords",
        )

        # Add a H1 section in the body
        figure.header.add_child(
            Element("{% if kwargs['title'] %}<style>h1 {text-align: center;}</style>{% endif %}"),
            name="h1_css_style",
        )
        figure.html.add_child(
            Element("{% if kwargs['title'] %}<h1>{{kwargs['title']}}</h1>{% endif %}"),
            name="h1_title",
        )

        # Modify the template of the figure to add the lang to the HTML document
        figure._template = Template(
            "<!DOCTYPE html>\n"
            "<html lang='en'>\n"  # <---- Modified here
            "<head>\n"
            "{% if this.title %}<title>{{this.title}}</title>{% endif %}"
            "    {{this.header.render(**kwargs)}}\n"
            "</head>\n"
            "<body>\n"
            "    {{this.html.render(**kwargs)}}\n"
            "</body>\n"
            "<script>\n"
            "    {{this.script.render(**kwargs)}}\n"
            "</script>\n"
            "</html>\n",
        )

        super().render(title=title, **kwargs)

        # Add custom css file (at the end of the header)
        # figure.header.add_child(
        #     CssLink(url="../css/custom.css", download=False), name="custom_css"
        # )


def prettify_network_name(name: str) -> tuple[int, str]:
    match = re.fullmatch(pattern=r"([0-9]{2})_MVFeeder([0-9]+)", string=name)
    assert match
    region_code = int(match.group(1))
    return (
        region_code,
        f"{FRENCH_REGIONS_CODES[region_code]} - MV Feeder {match.group(2)}",
    )


def main():
    console = Console()
    logging.basicConfig(level=logging.INFO, handlers=[RichHandler(console=console)], format="{message}", style="{")

    root = Path(__file__).parents[1]
    output_folderpath = root / "plots" / "networks"
    output_folderpath.mkdir(exist_ok=True, parents=True)

    logger.info("Start plotting the representative networks.")
    aggregated_buses_gdf = {}
    aggregated_lines_gdf = {}
    zoom_start = 12
    with Progress(
        SpinnerColumn(),
        *Progress.get_default_columns(),
        TimeElapsedColumn(),
        console=console,
        transient=False,
    ) as progress:
        files_to_convert = list((root / "data" / "networks").glob("*.json"))
        task = progress.add_task("[blue]Plotting the networks", total=len(files_to_convert))
        for p in files_to_convert:
            en = rlf.ElectricalNetwork.from_json(p)
            network_name = p.stem

            buses_gdf = en.buses_frame.reset_index()
            lines_gdf = en.lines_frame.reset_index()
            buses_gdf["network"] = network_name
            lines_gdf["network"] = network_name

            # Create the map
            region_code, title = prettify_network_name(name=network_name)
            m = RoseauMap(
                location=list(reversed(buses_gdf.union_all().centroid.coords[0])),
                zoom_start=zoom_start,
            )
            folium.GeoJson(
                data=lines_gdf,
                name="lines",
                marker=folium.CircleMarker(),
                style_function=lines_style_function,
                highlight_function=lines_highlight_function,
                tooltip=lines_tooltip,
            ).add_to(m)
            folium.GeoJson(
                data=buses_gdf,
                name="buses",
                marker=folium.CircleMarker(),
                style_function=buses_style_function,
                highlight_function=buses_highlight_function,
                tooltip=buses_tooltip,
            ).add_to(m)
            folium.LayerControl().add_to(m)

            # Save the map
            m.save(outfile=output_folderpath / f"{network_name}.html", title=title)

            # Aggregate the data frame
            aggregated_buses_gdf.setdefault(region_code, []).append(buses_gdf)
            aggregated_lines_gdf.setdefault(region_code, []).append(lines_gdf)

            # Update the progress bar
            progress.update(task, advance=1)

    logger.info("The representative networks have been successfully plotted.")

    # Create the regional maps
    logger.info("Start plotting the regional maps.")
    output_folderpath = root / "plots" / "regions"
    output_folderpath.mkdir(parents=True, exist_ok=True)

    with Progress(
        SpinnerColumn(),
        *Progress.get_default_columns(),
        TimeElapsedColumn(),
        console=console,
        transient=False,
    ) as progress:
        task = progress.add_task("[blue]Plotting the regions", total=len(aggregated_buses_gdf))
        for region_code, buses_gdf_list in aggregated_buses_gdf.items():
            lines_gdf_list = aggregated_lines_gdf[region_code]
            buses_gdf = pd.concat(objs=buses_gdf_list, ignore_index=True)
            lines_gdf = pd.concat(objs=lines_gdf_list, ignore_index=True)

            # Create the map
            m = RoseauMap(
                location=list(reversed(buses_gdf.union_all().centroid.coords[0])),
                zoom_start=9,
            )
            folium.GeoJson(
                data=lines_gdf,
                name="lines",
                marker=folium.CircleMarker(),
                style_function=lines_style_function,
                highlight_function=lines_highlight_function,
                tooltip=lines_tooltip_with_network,
            ).add_to(m)
            folium.GeoJson(
                data=buses_gdf,
                name="buses",
                marker=folium.CircleMarker(),
                style_function=buses_style_function,
                highlight_function=buses_highlight_function,
                tooltip=buses_tooltip_with_network,
            ).add_to(m)
            folium.LayerControl().add_to(m)

            # Hide the ReadTheDoc flyout in the resulting HTML file
            m.get_root().header.add_child(Element("<style> readthedocs-flyout { visibility: hidden; }</style>"))

            # Save the map
            region_name = FRENCH_REGIONS_CODES[region_code]
            filename = (
                unicodedata.normalize("NFKD", region_name)
                .encode("ASCII", "ignore")
                .decode()
                .replace("-", " ")
                .title()
                .replace(" ", "_")
                .replace("-", "_")
            )
            m.save(outfile=output_folderpath / f"{filename}.html", title=region_name)

            # Update the progress bar
            progress.update(task, advance=1)
    logger.info("The regional maps have been successfully plotted.")


if __name__ == "__main__":
    main()
