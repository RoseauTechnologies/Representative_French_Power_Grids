"""
This script is designed to download the archives of the representative Franch Power Grids, extract them in a
folder and convert them into a recent Roseau Load Flow JSON format.

The original data can be found here:
https://www.data.gouv.fr/fr/datasets/departs-hta-representatifs-pour-lanalyse-des-reseaux-de-distribution-francais/
"""

# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "requests>=2.32.3",
#     "rich>=14.0.0",
#     "roseau-load-flow>=0.13.1",
# ]
# ///

import io
import logging
import warnings
import zipfile
from pathlib import Path

import requests
import roseau.load_flow as rlf
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn

logger = logging.getLogger(__name__)

ARCHIVE_URL = "https://static.data.gouv.fr/resources/departs-hta-representatifs-pour-lanalyse-des-reseaux-de-distribution-francais/20241125-113327/departs-hta-representatifs.zip"
"""The static URL to download the network files in an old RLF format version."""


def main():
    console = Console()
    logging.basicConfig(level=logging.INFO, handlers=[RichHandler(console=console)], format="{message}", style="{")

    root = Path(__file__).parents[1]

    #
    # Download and extract the data from the source
    #
    extract_directory = root / "original_data"
    extract_directory.mkdir(exist_ok=True)
    logger.info("Start downloading the archive of networks files.")
    response = requests.get(url=ARCHIVE_URL, stream=True)
    response.raise_for_status()
    with io.BytesIO(response.content) as bio, zipfile.ZipFile(bio) as z:
        z.extractall(extract_directory)
    logger.info(f"The archive of networks files has been successfully downloaded and extracted in {extract_directory}.")

    #
    # Convert the files to the new format
    #
    logger.info("Start converting the original files into recent RLF files.")
    output_directory = root / "data" / "networks"
    files_to_convert = list(extract_directory.glob("*.json"))
    crs = "EPSG:4326"
    src_bus_id = "MVVoltage_source"

    with Progress(
        SpinnerColumn(), *Progress.get_default_columns(), TimeElapsedColumn(), console=console, transient=False
    ) as progress:
        task = progress.add_task("[blue]Converting the files", total=len(files_to_convert))
        for p in files_to_convert:
            # Ignore warnings because we open old RLF files
            with warnings.catch_warnings(action="ignore", category=UserWarning):
                en = rlf.ElectricalNetwork.from_json(p, include_results=False)

            # Patch the CRS
            en.crs = crs

            # Path the min and max voltage levels
            for bus in en.buses.values():
                if bus.id == src_bus_id:
                    # HV bus -> no min/max voltage level
                    continue
                elif bus.phases == "abc":
                    # MV buses
                    bus.nominal_voltage = 20e3  # V
                    bus.min_voltage_level = 0.95
                    bus.max_voltage_level = 1.05
                else:
                    # LV buses
                    assert bus.phases == "abcn"
                    bus.nominal_voltage = 400  # V
                    bus.min_voltage_level = 0.90
                    bus.max_voltage_level = 1.10

            # Adjust the name of the new files
            new_name = f"{p.stem.removesuffix('_load_adjusted')}{p.suffix}"

            # Remove the source bus and its switch and connect the source to the other bus of the
            # switch. The wye source can now have a floating neutral so no need to add "abcn" bus
            # for it.
            en_data = en.to_dict(include_results=False)
            (src,) = en_data["sources"]
            assert src["bus"] == src_bus_id, "The source should be connected to the MVVoltage_source bus"
            sw = en_data["switches"].pop()
            assert not en_data["switches"], "There should be only one switch"
            assert src["bus"] == sw["bus1"], "The source should be connected to the first bus of the switch"
            src["bus"] = sw["bus2"]
            for i, bus in enumerate(en_data["buses"]):
                if bus["id"] == src_bus_id:
                    assert bus["phases"] == "abcn", "The source bus should be an 'abcn' bus"
                    old_source_bus_idx = i
                    break
            else:
                raise AssertionError("The MVVoltage_source bus should be present")
            del en_data["buses"][old_source_bus_idx]
            for gc in en_data["ground_connections"]:
                if gc["element"]["type"] == "bus" and gc["element"]["id"] == src_bus_id:
                    gc["element"]["type"] = rlf.VoltageSource.element_type
                    gc["element"]["id"] = src["id"]
                    break
            else:
                raise AssertionError("The ground connection of the source should be present")
            en = rlf.ElectricalNetwork.from_dict(en_data, include_results=False)  # make sure everything is fine

            # Save the file using the last available Json format
            en.to_json(output_directory / new_name, include_results=False)

            # Update the progress bar
            progress.update(task, advance=1)
    logger.info("The original files have been successfully converted into recent RLF files.")


if __name__ == "__main__":
    main()
