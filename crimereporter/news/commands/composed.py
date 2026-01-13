from pathlib import Path
from typing import Iterator

from crimereporter.news.commands.commands import Command


class ComposedCommand(Command):
    """A command composed of multiple other commands."""

    def __init__(self, commands: list[Command] | None = None) -> None:
        super().__init__()
        self.commands: list[Command] = list(commands) if commands else []

    def run(self) -> None:
        """Execute all contained commands in order, with logging."""
        for cmd in self.commands:
            cmd.execute()  # each subcommand logs its own start/finish/error

    def add(self, cmd: Command) -> None:
        """Add a command to the composition."""
        self.commands.append(cmd)

    def __or__(self, other: Command) -> "ComposedCommand":
        """Allow combining commands with the | operator."""
        if isinstance(other, ComposedCommand):
            return ComposedCommand(self.commands + other.commands)
        return ComposedCommand(self.commands + [other])

    def __iter__(self) -> Iterator[Command]:
        """Iterate over contained commands."""
        return iter(self.commands)

    def input_files(self) -> list[Path]:
        """Return a deduplicated list of input files from all subcommands."""
        files: set[Path] = set()
        for cmd in self.commands:
            files.update(cmd.input_files())
        return list(files)
