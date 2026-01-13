from crimereporter.news.commands.commands import logger
from crimereporter.news.commands.simple import SimpleCommand
from crimereporter.news.renderers.thumbnail import ThumbnailRenderer


class ThumbnailCommand(SimpleCommand):

    def run(self) -> None:
        filename = self.input_file.parent / "output" / f"{self.orientation}.png"
        if not self.should_run(filename):
            logger.info("Thumbnail already exists, skipping")
            return
        renderer = ThumbnailRenderer()
        renderer.render(self.script, self.orientation, filename)
