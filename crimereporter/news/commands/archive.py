import shutil
from pathlib import Path

from crimereporter.news.commands.commands import Command, logger
from crimereporter.utils.config import Config

config = Config()


class ArchiveCommand(Command):

    def run(self) -> None:
        logger.info("Archiving")

        ACTIVE_DIRECTORY = Path(config.programs) / Path("Active")
        ARCHIVE_DIRECTORY = Path(config.programs) / Path("Archive")

        # Ensure the archive directory exists
        ARCHIVE_DIRECTORY.mkdir(parents=True, exist_ok=True)

        # Move each directory inside Active to Archive
        for item in ACTIVE_DIRECTORY.iterdir():
            if item.is_dir():
                logger.info(f"Archiving {item.name}")
                shutil.move(str(item), ARCHIVE_DIRECTORY / item.name)
