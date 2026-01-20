import logging
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from jinja2 import Template

from crimereporter.ai.ai_engine import AIEngine
from crimereporter.grabber.article import Article
from crimereporter.news.commands.commands import Command
from crimereporter.utils.config import Config
from crimereporter.utils.templates import env

logger = logging.getLogger(__name__)
ai_logger = logging.getLogger("call.logger.ai")
config = Config()
Path(f"{Path(config.root)}/log").mkdir(parents=True, exist_ok=True)


class AICommand(Command, ABC):
    def __init__(self, script: int):
        super().__init__()
        self.script = script
        self.script_directory = Path(config.root) / f"programs/Active/{script:05d}"
        self.target_file = self.script_directory / "script.yaml"
        self.question_file = self.script_directory / "question.txt"
        self.engine: AIEngine = AIEngine.create(config.ai_command)
        self.target_yaml = Path("templates/script.yaml").read_text(encoding="utf-8")

    def run(self) -> None:
        """Generate script using the AI engine and copy files."""
        if self.target_file.exists() and self.question_file.exists():
            logger.info("Script %s generated", self.target_file)
            return
        self.script_directory.mkdir(parents=True, exist_ok=True)
        message = self.template.render(self.payload)
        logger.info(f"Save QUESTION {self.question_file}")
        self.question_file.write_text(message, encoding="utf-8")
        logger.info("Send message to AI engine")
        response_text = self.engine.generate(message)
        ai_logger.info(f"{self.engine.name}, {len(message)}, {len(response_text)}")
        logger.info("Save response to %s", self.target_file)

        self.script_directory.mkdir(parents=True, exist_ok=True)
        self.target_file.write_text(response_text, encoding="utf-8")
        self.copy_files()

    def input_files(self) -> list[Path]:
        files = super().input_files()
        files.append(Path(self.template.filename))
        return files

    @property
    @abstractmethod
    def template(self) -> Template:
        pass

    @property
    @abstractmethod
    def payload(self) -> dict[str, Any]:
        pass

    @abstractmethod
    def copy_files(self) -> None:
        pass


class AIDownloadCommand(AICommand):
    """Command that generates a script using OpenAI based on an article."""

    def __init__(self, force: str, identifier: str, script: int) -> None:
        super().__init__(script)
        self.force = force
        self.id = identifier
        self.source_yaml_filename = self.get_yaml_file_name()
        self.article = Article.load_from_yaml(self.source_yaml_filename)
        self.source_directory = self.source_yaml_filename.parent

    def get_yaml_file_name(self) -> Path:
        downloads_path = Path(config.root) / "downloads"
        pattern = f"*/*/*/{self.force}/{self.id}/article.yaml"
        files = list(downloads_path.glob(pattern))

        if not files:
            raise FileNotFoundError(f"{self.force}/{self.id}/article.yaml not found")

        # pick the latest by path ordering (works if YYYY/MM/DD format is used)
        latest_file = max(files, key=str)
        return latest_file

    @property
    def template(self) -> Template:
        return env.get_template("ai.download.question")

    @property
    def payload(self) -> dict[str, Any]:
        return {
            "text": self.article.article,
            "url": self.article.url,
            "date": self.article.timestamp[0:10],
            "source": self.article.source_name,
            "identifier": self.article.identifier,
            "title": self.article.title,
            "yaml": self.target_yaml,
            "files": self.article.files,
        }

    def copy_files(self) -> None:
        """Copy all files referenced in the article to the script directory."""
        image_extensions = tuple(config.image_extensions)
        for image_file in self.source_directory.rglob("*"):
            if image_file.suffix.lower() not in image_extensions:
                continue
            if not image_file.is_file():
                continue
            logger.info("Copy image %s to %s", image_file, self.script_directory)
            shutil.copy(image_file, self.script_directory)


class AITextCommand(AICommand):
    """Command that generates a script using OpenAI based on a text."""

    def __init__(self, script: int) -> None:
        super().__init__(script)
        self.source_text = self.script_directory / "source.txt"

    @property
    def template(self) -> Template:
        return env.get_template("ai.text.question")

    def image_filenames(self) -> list[str]:
        return sorted(
            image_file.name
            for image_file in self.script_directory.rglob("*")
            if image_file.suffix.lower() in config.image_extensions
        )

    @property
    def payload(self) -> dict[str, Any]:
        return {
            "text": self.source_text.read_text(encoding="utf-8"),
            "yaml": self.target_yaml,
            "files": self.image_filenames(),
        }

    def copy_files(self) -> None:
        return

    def input_files(self) -> list[Path]:
        return []
