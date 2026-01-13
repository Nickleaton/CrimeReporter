from pathlib import Path

from crimereporter.news.commands.commands import Command
from crimereporter.news.script import Script


class SimpleCommand(Command):
    """Base for commands that operate on a script file."""

    def __init__(self, filename: Path, orientation: str) -> None:
        super().__init__()
        self.input_file = filename
        self.orientation = orientation
        self.script = Script(self.input_file)

    def input_files(self) -> list[Path]:
        files = super().input_files()
        files.append(self.input_file)
        return files
