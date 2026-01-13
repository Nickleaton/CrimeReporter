from pathlib import Path

from crimereporter.news.renderers.renderer import Renderer
from crimereporter.news.script import Script, logger
from crimereporter.utils.templates import env


class DescriptionRender(Renderer):
    """Renderer that outputs the script as plain text."""

    def render(self, script: Script, orientation: str, output_path: Path) -> None:
        """Render the script as wrapped text to the specified file path."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        parent_name = output_path.parent.parent.name
        context = {**script.parsed, "parent_name": parent_name}
        text = env.get_template("description.txt").render(**context)

        logger.info(f"Saving text output to {output_path} ({len(text)} characters)")

        # Write to file
        output_path.write_text(text, encoding="utf-8")
