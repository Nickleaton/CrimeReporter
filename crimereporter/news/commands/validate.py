from datetime import datetime
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse

import strictyaml
from strictyaml import YAMLValidationError

from crimereporter.news.commands.commands import Command, config, logger
from crimereporter.news.script_schema import SCHEMA


# crimereporter/news/commands/exceptions.py
class ValidationError(Exception):
    """Raised when YAML or content validation fails (IDE-friendly)."""

    def __init__(self, message: str, filename: str | Path | None = None, line: int | None = None):
        self.filename = filename
        self.line = line
        self.message = message
        super().__init__(self.__str__())

    def __str__(self) -> str:
        if self.filename and self.line is not None:
            return f"{self.filename}:{self.line}:0: {self.message}"
        return self.message


class ValidateCommand(Command):

    def __init__(self, filename: Path, orientation: str) -> None:
        super().__init__()
        self.input_file = filename
        self.directory = filename.parent
        self.orientation = orientation
        # Map fields to their validation methods
        self.field_validators: dict[str, Callable] = {
            "Image": self.validate_image,
            "Video": self.validate_video,
            "Audio": self.validate_audio,
            "Still": self.validate_still,
            "Text": self.validate_text,
        }

    def run(self) -> None:
        """Validate the YAML file and raise an error if invalid."""
        if not self.input_file.exists():
            logger.error(f"YAML file {self.input_file} doesn't exist")
            raise FileNotFoundError(f"YAML file {self.input_file} doesn't exist")
        # --- Read file ---
        try:
            self.content = self.input_file.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to read YAML file {self.input_file}: {e}")
            raise e

        self.validate_schema()
        self.validate_lengths()
        self.validate_dates()
        self.validate_urls()
        self.validate_files()
        self.validate_segments()

    def check_file(self, filename):
        if not (self.directory / filename).exists():
            logger.error(f"File {filename} doesn't exist in {self.directory}")
            raise FileNotFoundError(f"File {filename} doesn't exist in {self.directory}")

    def validate_schema(self) -> None:
        """Validate the YAML structure against the schema and report concise errors."""
        try:
            self.data = strictyaml.load(self.content, SCHEMA)
        except YAMLValidationError as e:
            mark = getattr(e, "problem_mark", None)
            line_no = mark.line + 1 if mark else None
            column = mark.column if mark else None
            message = e.problem or str(e)

            logger.error(f"{self.input_file}:{line_no}:{column}: {message}")
            raise ValidationError(message, filename=self.input_file, line=line_no)

    def validate_lengths(self):
        # Title
        title_node = self.data["Title"]
        if len(title_node.data) > config.validation.maximum_title:
            message = f"Title in {self.input_file} is too long"
            logger.error(message)
            raise ValidationError(message, filename=self.input_file, line=title_node.start_line)

        # Description
        desc_node = self.data["Description"]
        if len(desc_node.data) > config.validation.maximum_description:
            message = f"Description in {self.input_file} is too long"
            logger.error(message)
            raise ValidationError(message, filename=self.input_file, line=desc_node.start_line)

    def validate_file(self, filename: str, line: int):
        """Validate a file exists, raising ValidationError with line/column info."""
        file_path = self.directory / filename
        if file_path.is_dir():
            message = "No file specified. Empty?"
            logger.error(message)
            raise ValidationError(message, filename=self.input_file, line=line)

        if not file_path.exists():
            message = f"File {filename} doesn't exist in {self.directory}"
            logger.error(message)
            raise ValidationError(message, filename=self.input_file, line=line)

    def validate_files(self):
        thumb_node = self.data["Thumbnail"]
        filename = thumb_node.data
        line = thumb_node.start_line
        self.validate_file(filename, line)

    def validate_image(self, seg):
        node = seg["Image"]  # YAML node
        filename = node.data

        if not filename:
            raise ValidationError(
                "Image filename is empty",
                filename=self.input_file,
                line=node.start_line,
            )
        self.validate_file(filename, node.start_line)

    def validate_video(self, seg):
        node = seg["Video"]
        data = node.data

        # Handle dict or string
        if isinstance(data, dict):
            filename = data.get("Filename")
        else:
            filename = data  # assume direct string

        if not filename:
            raise ValidationError("Video filename missing", filename=self.input_file, line=node.start_line)

        self.validate_file(filename, node.start_line)

    def validate_audio(self, seg):
        node = seg["Audio"]
        data = node.data

        if isinstance(data, dict):
            filename = data.get("Filename")
        else:
            filename = data

        if not filename:
            raise ValidationError("Audio filename missing", filename=self.input_file, line=node.start_line)

        self.validate_file(filename, node.start_line)

    def validate_still(self, seg):
        node = seg["Still"]
        data = node.data

        if not isinstance(data, dict) or "Filename" not in data:
            raise ValidationError("Still filename missing", filename=self.input_file, line=node.start_line)

        filename = data["Filename"]
        self.validate_file(filename, node.start_line)

    def validate_text(self, seg):
        node = seg["Text"]
        if not node.data.strip():
            raise ValidationError("Text content missing", filename=self.input_file, line=node.start_line)

    def validate_segment(self, seg):
        """
        Validate a single segment (StrictYAML objects):
        - Exactly one media: Image, Video, Still
        - Optional content: Text or Audio (max one)
        - Validate existence of files
        """
        # Dispatch loop
        for field, validator in self.field_validators.items():
            if field in seg:
                validator(seg)

    def validate_segments(self):
        """
        Validate all segments in self.data['Segments'] using StrictYAML objects.
        No manual line needed; each field carries its own line info.
        """
        for segment in self.data["Segments"]:
            seg_dict = segment["Segment"]
            self.validate_segment(seg_dict)

    def validate_url(self, node):
        """Validate that the URL is properly formed."""
        url = node.data
        parsed_url = urlparse(url)
        if not (parsed_url.scheme in ("http", "https") and parsed_url.netloc):
            message = f"Invalid URL: {url}"
            logger.error(message)
            raise ValidationError(message, filename=self.input_file, line=node.start_line)

    def validate_urls(self):
        self.validate_url(self.data["URL"])

    def validate_date(self, node):
        """Validate the date format is YYYY-MM-DD."""
        date = node.data
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            message = f"Invalid date format: {date}"
            logger.error(message)
            raise ValidationError(message, filename=self.input_file, line=node.start_line)

    def validate_dates(self):
        self.validate_date(self.data["Date"])
