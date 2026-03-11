from pathlib import Path

from crimereporter.utils.config import Config

config = Config()


class Directories:
    DIRECTORY = Path(config.root) / "programs"

    @staticmethod
    def get_programs_from_directory(search_dir: Path) -> list[int]:
        """Return a sorted list of numeric subdirectory names under the given directory."""

        if not search_dir.is_dir():
            raise NotADirectoryError(f"{search_dir} is not a valid directory.")

        numeric_dirs = [
            int(d.name) for d in search_dir.iterdir() if d.is_dir() and d.name.isdigit()
        ]
        return sorted(numeric_dirs)

    @staticmethod
    def get_active_programs() -> list[int]:
        """Return a sorted list of available Active scripts."""
        return Directories.get_programs_from_directory(Directories.DIRECTORY / "Active")

    @staticmethod
    def get_archive_programs() -> list[int]:
        """Return a sorted list of available Archive scripts."""
        return Directories.get_programs_from_directory(Directories.DIRECTORY / "Archive")

    @staticmethod
    def get_all_programs() -> list[int]:
        """Return all numeric program directories under programs/*."""
        programs = set()

        for category in Directories.DIRECTORY.iterdir():
            if not category.is_dir():
                continue

            for d in category.iterdir():
                if d.is_dir() and d.name.isdigit():
                    programs.add(int(d.name))

        return sorted(programs)

    @staticmethod
    def get_newest_active_program() -> int:
        """Return the largest numeric directory under Active."""
        programs = Directories.get_active_programs()
        if not programs:
            return 0
        return programs[-1]

    @staticmethod
    def get_oldest_active_program() -> int:
        """Return the smallest numeric directory under Active."""
        programs = Directories.get_active_programs()
        return programs[0] if programs else 0

    @staticmethod
    def get_newest_archive_program() -> int:
        """Return the largest numeric directory under Archive."""
        programs = Directories.get_archive_programs()
        if not programs:
            return 0
        return programs[-1]

    @staticmethod
    def get_oldest_archive_program() -> int:
        """Return the smallest numeric directory under Archive."""
        programs = Directories.get_archive_programs()
        return programs[0] if programs else 0

    @staticmethod
    def get_next_program() -> int:
        """Return the smallest missing program number, or max + 1."""
        programs = set(Directories.get_all_programs())
        i = 1
        while i in programs:
            i += 1
        return i
