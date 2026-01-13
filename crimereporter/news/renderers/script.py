import re
import textwrap
from pathlib import Path

from crimereporter.news.renderers.renderer import Renderer
from crimereporter.news.script import Script, logger


class ScriptRender(Renderer):
    """Renderer that outputs the script as plain text."""

    def render(self, script: Script, orientation: str, output_path: Path) -> None:
        """Render the script as wrapped text to the specified file path."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Join all segments into a single string
        text = "".join(seg["text"] for seg in script.segments if "text" in seg)

        # strip out markup

        text = re.sub(r"<phoneme[^>]*>", "", text)
        # Remove closing </phoneme> tags
        text = re.sub(r"</phoneme>", "", text)

        # Wrap text to 80 characters
        wrapped_text = textwrap.fill(text, width=80)

        logger.info(f"Saving text output to {output_path} ({len(text)} characters)")

        # Write to file
        output_path.write_text(wrapped_text, encoding="utf-8")
