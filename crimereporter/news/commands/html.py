import webbrowser

from crimereporter.news.commands.commands import logger
from crimereporter.news.commands.simple import SimpleCommand
from crimereporter.news.renderers.html import HTMLRenderer


class HTMLCommand(SimpleCommand):

    def run(self) -> None:
        filename = self.input_file.parent / "output/story.html"
        if not self.should_run(filename):
            logger.info("HTML already exists, skipping")
            return
        renderer = HTMLRenderer()
        renderer.render(self.script, self.orientation, filename)
        webbrowser.open(str(filename))
