from crimereporter.news.commands.commands import logger
from crimereporter.news.commands.simple import SimpleCommand
from crimereporter.news.renderers.description import DescriptionRender
from crimereporter.news.renderers.script import ScriptRender


class TextCommand(SimpleCommand):

    def run(self) -> None:
        script_filename = self.input_file.parent / "output/text.txt"
        if self.should_run(script_filename):
            script_renderer = ScriptRender()
            script_renderer.render(self.script, self.orientation, script_filename)
        else:
            logger.info("Script already exists, skipping")

        description_filename = self.input_file.parent / "output/description.txt"
        if self.should_run(description_filename):
            description_renderer = DescriptionRender()
            description_renderer.render(self.script, self.orientation, description_filename)
        else:
            logger.info("Description already exists, skipping")
