import logging
import re
from pathlib import Path

import strictyaml
from strictyaml import YAMLError

from crimereporter.news.script_schema import SCHEMA
from crimereporter.utils.templates import env

logger = logging.getLogger(__name__)


class Script:
    """
    Represents a news script parsed from YAML with title, files, text segments,
    tokenized transcript, and optional timestamps.
    """

    TOKEN_REGEX = re.compile(
        r"""
        \d{1,2}(?:st|nd|rd|th)                                  # ordinals like 1st, 2nd
        |\d{1,3}(?:,\d{3})*(?:\.\d+)?(?:-\w+)*(?:[.,!?;:]*)?    # numbers w/ commas, decimals, hyphenated
        |\w+(?:'\w+|')?(?:[.,!?;:]*)?                           # words w/ contractions or trailing apostrophe
        |[^\w\s]                                                # standalone punctuation
        """,
        re.UNICODE | re.VERBOSE,
    )

    def __init__(self, filepath: Path):
        super().__init__()
        self.filepath = filepath
        self.directory = filepath.parent
        self.title = ""

        # handle archives
        if not self.filepath.exists():
            return
        logger.info(f"Loading script  {filepath}")

        with open(self.filepath, encoding="utf-8") as f:
            raw_text = f.read()

        # --- Try 1: Read file ---
        try:
            with open(self.filepath, encoding="utf-8") as f:
                raw_text = f.read()
        except (OSError, UnicodeDecodeError) as e:
            logger.error(f"File error while reading {self.filepath}: {e}")
            raise  # re-raise original exception

        # --- Try 2: Parse YAML ---
        try:
            self.parsed = strictyaml.load(raw_text, SCHEMA).data
        except YAMLError as e:
            logger.error(f"YAML validation error in {self.filepath}:\n{e}")
            raise  # re-raise original exception

        logger.info(f"Successfully loaded {self.filepath}")

    @classmethod
    def tokenize(cls, text: str) -> list[str]:
        """Tokenize a string into words, numbers, contractions, punctuation."""
        return cls.TOKEN_REGEX.findall(text)

    @property
    def segments(self):
        """Yield segments directly from parsed YAML, adding tokens + timestamp."""
        for seg in self.parsed["Segments"]:
            seg_data = seg["Segment"]
            result = {}

            if "Image" in seg_data:
                result["image"] = seg_data["Image"]
            if "Video" in seg_data:
                result["video"] = seg_data["Video"]
            if "Text" in seg_data:
                result["text"] = seg_data["Text"]
                result["tokens"] = self.tokenize(seg_data["Text"])
            if "Audio" in seg_data:
                result["audio"] = seg_data["Audio"]

            # Always include timestamp field (can be None)
            result["timestamp"] = None
            yield result

    def all_tokens(self):
        """Return all tokens across segments with provenance."""
        tokens = []
        for seg_idx, segment in enumerate(self.segments):
            for tok_idx, tok in enumerate(segment["tokens"]):
                tokens.append((seg_idx, tok_idx, tok))
        return tokens

    def description(self) -> str:
        template = env.get_template("description.txt")
        return template.render(**self.parsed)

    @property
    def type_name(self) -> str:
        return self.parsed["Type"]

    def __repr__(self):
        return f"<Script title={self.title} segments={len(list(self.segments))}>"
