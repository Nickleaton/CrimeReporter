import re
from pathlib import Path

from strictyaml import Map, Seq, Str, load

PHONEME_SCHEMA = Map({"phonemes": Seq(Str())})


class PhonemeSubstitutor:
    TAG_INNER_TEXT = re.compile(r">\s*([^<]+?)\s*<")

    def __init__(self, yaml_path: str | Path):
        self.rules = self.load_rules(yaml_path)

    def load_rules(self, yaml_path: str | Path) -> list[tuple[re.Pattern[str], str]]:
        yaml_text = Path(yaml_path).read_text(encoding="utf-8")
        parsed = load(yaml_text, PHONEME_SCHEMA)

        rules: list[tuple[re.Pattern[str], str]] = []

        for entry in parsed["phonemes"].data:
            match = self.TAG_INNER_TEXT.search(entry)
            if not match:
                raise ValueError(f"Phoneme entry must contain inner text: {entry}")

            source = match.group(1)

            pattern = re.compile(
                r"\b" + re.escape(source) + r"\b",
                flags=re.IGNORECASE,
            )

            rules.append((pattern, entry))

        return rules

    def substitute(self, text: str) -> str:
        for source, target in self.rules:
            pattern = r"\b" + re.escape(source) + r"\b"

            def repl(match):
                original = match.group(0)
                return re.sub(
                    re.escape(source),
                    original,
                    target,
                    flags=re.IGNORECASE,
                )

            text = re.sub(pattern, repl, text, flags=re.IGNORECASE)

        return text
