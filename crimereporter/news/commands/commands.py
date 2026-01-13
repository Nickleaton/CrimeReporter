import logging
from abc import ABC
from pathlib import Path

from crimereporter.utils.config import Config

logger = logging.getLogger(__name__)

config = Config()


class Command(ABC):
    """Base class for all commands."""

    def __init__(self) -> None:
        self.name = self.__class__.__name__

    def execute(self) -> None:
        """Template method: log start/finish and handle errors."""
        self.run()

    def run(self) -> None:
        """Subclasses must implement this method."""
        raise NotImplementedError(f"{self.name} must implement run()")

    def input_files(self) -> list[Path]:
        """
        Return a list of input files that this task depends on.

        Subclasses should extend this list by including any additional
        files that they rely on. Parent class files can be included by
        calling `super().input_files()`.

        Returns:
            list[Path]: A list of Path objects pointing to input files
                        relevant to this task. Missing files are allowed;
                        `should_run` will handle them appropriately.
        """
        return [Path("configuration/config.yaml"), Path("images/logo.png")]

    def should_run(self, filename: Path) -> bool:
        """
        Determine if the process should run based on the modification times
        of input files compared to a reference file.

        Returns True if:
          - The reference file doesn't exist.
          - There are no input files.
          - Any input file is newer than the reference.
        """
        if not filename.exists():
            logger.info(f"File exists {filename}")
            return True

        inputs = self.input_files()
        if not inputs:
            logger.info(f"No input files for {self.name}")
            return True
        ref_time = filename.stat().st_mtime
        for inp in inputs:
            if not inp.exists():
                logger.warning(f"Input file {inp} doesn't exist")
                continue
            if inp.stat().st_mtime > ref_time:
                logger.info(f"Input file {inp} is newer than {filename}")
                return True
        return False
