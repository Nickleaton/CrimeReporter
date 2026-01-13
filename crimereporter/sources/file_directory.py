import logging
from pathlib import Path
from typing import Self

from crimereporter.sources.file_record import FileRecord

logger = logging.getLogger(__name__)


class FileDirectory:
    """
    Represents a collection of FileRecords for an article.

    Invariants:
        - All elements of self.records are FileRecord instances.
        - Filenames in self.records are unique.
    """

    def __init__(self, records: list[FileRecord] = None):
        """
        Construct a FileDirectory.

        Preconditions:
            - If records is provided, all elements must be FileRecord instances.
        """
        if records is not None and not all(isinstance(r, FileRecord) for r in records):
            raise TypeError("All elements of records must be FileRecord instances")
        self.records: list[FileRecord] = list(records) if records else []

    def add(self, record: FileRecord):
        """
        Add a FileRecord to the collection.

        Preconditions:
            - record must be a FileRecord instance.
        Postconditions:
            - record is appended to self.records.
        """
        if not isinstance(record, FileRecord):
            raise TypeError("record must be a FileRecord instance")
        self.records.append(record)

    def verify_unique_filenames(self):
        """
        Verify that all filenames in the collection are unique.

        Preconditions:
            - self.records is not None
        Postconditions:
            - No duplicate filenames exist in self.records

        Raises:
            ValueError: If duplicate filenames are found.
        """
        seen = set()
        duplicates = set()
        for rec in self.records:
            if rec.filename in seen:
                duplicates.add(rec.filename)
            else:
                seen.add(rec.filename)

        if duplicates:
            raise ValueError(f"Duplicate filenames found in FileDirectory: {duplicates}")

    def save(self, directory: Path) -> list[Path]:
        """
        Save all FileRecords to the specified directory.

        Preconditions:
            - directory must be a valid Path object (not None)
            - self.records contains only valid FileRecord instances
        Postconditions:
            - Each FileRecord is saved to the directory
            - Returns a list of Paths to all saved files
            - Raises if any FileRecord fails to save (all-or-nothing behavior)

        Args:
            directory (Path): Target directory where all files are saved.

        Returns:
            List[Path]: List of paths to the saved files.
        """
        if directory is None:
            raise ValueError("directory must be provided")
        self.verify_unique_filenames()

        saved_paths = []
        for rec in self.records:
            try:
                path = rec.save(directory)
                saved_paths.append(path)
            except Exception as e:
                logger.error(f"Failed to save file {rec.filename}: {e}")
                raise  # propagate failure to ensure postconditions are not silently violated

        return saved_paths

    def __iter__(self):
        """Allow iteration over FileRecords."""
        return iter(self.records)

    def __len__(self):
        """Return the number of FileRecords."""
        return len(self.records)

    def __repr__(self):
        """
        Developer-friendly representation.

        Shows count and a preview of up to 5 filenames for debugging.
        """
        preview = [rec.filename for rec in self.records[:5]]
        more = "..." if len(self.records) > 5 else ""
        return f"<FileDirectory {len(self.records)} files: {preview}{more}>"

    # --- Merging using | operator ---
    def __or__(self, other: Self | FileRecord) -> Self:
        """
        Merge with another FileDirectory or a single FileRecord using | operator.
        Raises ValueError if duplicate filenames occur.
        """
        if isinstance(other, FileDirectory):
            merged_records = self.records + other.records
        elif isinstance(other, FileRecord):
            merged_records = self.records + [other]
        else:
            return NotImplemented

        merged_dir = FileDirectory(merged_records)
        # merged_dir.verify_unique_filenames()
        return merged_dir

    def __ior__(self, other: Self | FileRecord) -> Self:
        """
        In-place merge with another FileDirectory or FileRecord using |= operator.
        """
        if isinstance(other, FileDirectory):
            self.records.extend(other.records)
        elif isinstance(other, FileRecord):
            self.records.append(other)
        else:
            return NotImplemented

        # self.verify_unique_filenames()
        return self

    def __str__(self) -> str:
        """
        User-friendly string representation: one filename per line.
        """
        return "\n".join(rec.filename for rec in self.records)
