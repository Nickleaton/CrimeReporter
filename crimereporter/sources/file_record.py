import logging
from enum import Enum, auto
from pathlib import Path

logger = logging.getLogger(__name__)


class FileType(Enum):
    IMAGE = auto()
    EMBEDDED = auto()
    ZIP_MEMBER = auto()
    VIDEO = auto()


class FileRecord:
    """
    Represents a single file associated with an article.

    Attributes:
        filename (str): Suggested name for the file (used when saving).
        file_type (FileType): Classification of the file type.
        content (bytes): File content in memory (must not be None).
        source (str): Reference or annotation describing where the content was obtained.
    """

    def __init__(self, filename: str, file_type: FileType, content: bytes, source: str):
        """
        Construct a FileRecord.

        Preconditions:
            - filename is a non-empty string and contains no path separators.
            - file_type is a valid FileType.
            - content is bytes and not None.
            - source is a string.

        Invariants:
            - content is never None.
        """
        # Preconditions
        if not isinstance(filename, str) or not filename:
            raise ValueError("filename must be a non-empty string")
        if Path(filename).name != filename:
            raise ValueError("filename must not contain path components")
        if not isinstance(file_type, FileType):
            raise TypeError("file_type must be an instance of FileType")
        if not isinstance(content, bytes):
            raise TypeError("content must be bytes")
        if not isinstance(source, str):
            raise TypeError("source must be a string")

        # Assign fields
        self.filename = filename
        self.file_type = file_type
        self.content = content
        self.source = source

    def save(self, directory: Path) -> Path:
        """
        Save the file to the specified directory.

        Preconditions:
            - directory must be provided (non-None).

        Postconditions:
            - A file exists at the returned path containing the content of this FileRecord.

        Args:
            directory (Path): Target directory to save the file.

        Returns:
            Path: Path to the saved file.
        """
        if directory is None:
            raise ValueError("directory must be provided")

        # Ensure the target directory exists
        directory.mkdir(parents=True, exist_ok=True)

        target_path = directory / self.filename
        logger.info(f"Saving file to directory: {target_path}")
        target_path.write_bytes(self.content)

        return target_path

    def __repr__(self) -> str:
        """Developer-friendly string representation."""
        return f"<FileRecord filename={self.filename!r} " f"type={self.file_type.name} " f"source={self.source!r}>"
