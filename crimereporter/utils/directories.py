from pathlib import Path

from crimereporter.utils.config import Config

config = Config()


class Directories:
    ACTIVE_DIRECTORY = Path(config.programs) / Path("Active")
    ARCHIVE_DIRECTORY = Path(config.programs) / Path("Archive")

    @staticmethod
    def get_programs_from_directory(search_dir: Path) -> list[int]:
        """Return a sorted list of numeric subdirectory names under the given directory."""

        if not search_dir.is_dir():
            raise NotADirectoryError(f"{search_dir} is not a valid directory.")

        numeric_dirs = [int(d.name) for d in search_dir.iterdir() if d.is_dir() and d.name.isdigit()]
        return sorted(numeric_dirs)

    @staticmethod
    def get_active_programs() -> list[int]:
        """Return a sorted list of available Active scripts."""
        return Directories.get_programs_from_directory(Directories.ACTIVE_DIRECTORY)

    @staticmethod
    def get_archive_programs() -> list[int]:
        """Return a sorted list of available Active scripts."""
        return Directories.get_programs_from_directory(Directories.ARCHIVE_DIRECTORY)

    @staticmethod
    def get_newest_active_program() -> int:
        """Return the largest numeric directory under Active."""
        programs = Directories.get_active_programs()
        if len(programs) == 0:
            return 0
        return Directories.get_active_programs()[-1]

    @staticmethod
    def get_oldest_active_program() -> int:
        """Return the smallest numeric directory under Active."""
        return Directories.get_active_programs()[0]

    @staticmethod
    def get_newest_archive_program() -> int:
        """Return the largest numeric directory under Archive."""
        programs = Directories.get_archive_programs()
        if len(programs) == 0:
            return 0
        return Directories.get_archive_programs()[-1]

    @staticmethod
    def get_oldest_archive_program() -> int:
        """Return the smallest numeric directory under Archive."""
        return Directories.get_archive_programs()[0]

    @staticmethod
    def get_next_program() -> int:
        active: int = Directories.get_newest_active_program()
        archive: int = Directories.get_newest_archive_program()
        return max(active, archive) + 1
