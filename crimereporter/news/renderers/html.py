from datetime import datetime
from pathlib import Path

from crimereporter.news.renderers.renderer import Renderer
from crimereporter.news.script import Script, logger
from crimereporter.utils.templates import env


class HTMLRenderer(Renderer):
    """Renderer that outputs the script as HTML using a Jinja2 template."""

    @staticmethod
    def resolve_image(path: str) -> str:
        """Return an image path, falling back to files/{filename} if not found."""
        p = Path(path)
        if p.exists():
            return str(p)
        return f"files/{p.name}"

    def render(self, script: Script, orientation: str, output_path: Path) -> None:
        """Render the script to HTML and save it to the specified file path."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Path to the template file
        template = env.get_template("news_story.html")

        output = template.render(
            **script.parsed,
            current_year=datetime.now().year,
            resolve_image=self.resolve_image,  # fixed reference
        )

        logger.info(f"Saving HTML output to {output_path} ({len(output)} characters)")

        # Write to file
        output_path.write_text(output, encoding="utf-8")
