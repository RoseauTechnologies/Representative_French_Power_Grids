# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "requests>=2.32.3",
#     "rich>=14.0.0",
#     "roseau-load-flow>=0.13.1",
# ]
# ///

import logging
import warnings
from pathlib import Path

import roseau.load_flow as rlf
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn

logger = logging.getLogger(__name__)


def main():
    console = Console()
    logging.basicConfig(level=logging.INFO, handlers=[RichHandler(console=console)], format="{message}", style="{")

    root = Path(__file__).parents[1]

    #
    # Iterate on the networks to update the file version
    #
    logger.info("Start updating the files into recent RLF files.")
    output_directory = root / "data" / "networks"
    files_to_convert = list(output_directory.glob("*.json"))

    with Progress(
        SpinnerColumn(), *Progress.get_default_columns(), TimeElapsedColumn(), console=console, transient=False
    ) as progress:
        task = progress.add_task("[blue]Updating the files", total=len(files_to_convert))
        for p in files_to_convert:  # type:Path
            with warnings.catch_warnings():
                # Ignore warnings because we open old RLF files
                warnings.simplefilter(action="ignore", category=UserWarning)
                en = rlf.ElectricalNetwork.from_json(p, include_results=False)

            # Save the file using the last available Json format
            en.to_json(p, include_results=False)

            # Update the progress bar
            progress.update(task, advance=1)
    logger.info("The files have been successfully updated into recent RLF files.")


if __name__ == "__main__":
    main()
