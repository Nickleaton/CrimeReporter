import shutil
from pathlib import Path

from crimereporter.news.commands.commands import Command, logger
from crimereporter.utils.config import Config

config = Config()


class TemplateCommand(Command):

    def __init__(self, program: int):
        super().__init__()
        self.program = program

    def run(self) -> None:
        programs = Path(config.programs)
        script_path = Path("templates/script.yaml")
        active_dir = programs / "Active"
        path = active_dir / f"{self.program:05d}"
        logger.info("Creating %s", path)
        path.mkdir(parents=True, exist_ok=True)
        shutil.copy(script_path, path / script_path.name)
        logger.info("Copied %s to %s", script_path, path)
