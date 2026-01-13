import logging
from abc import abstractmethod

from crimereporter.utils.config import Config

logger = logging.getLogger(__name__)

config = Config()


class Command:
    """Base class for all commands."""

    def __init__(self) -> None:
        """
        Initialize the command with a name.
        """
        if self.__class__.__name__ == "Command":
            self.name = self.__class__.__name__
        else:
            self.name = self.__class__.__name__.removesuffix("Command")

    @abstractmethod
    def execute(self) -> None:
        """Execute the command. To be overridden by subclasses."""
        pass


class ComposedCommand(Command):

    def __init__(self, commands: list[Command]) -> None:
        super().__init__()
        self.commands = commands

    def execute(self) -> None:
        for command in self.commands:
            command.execute()
