import os
import platform

from crimereporter.news.commands.commands import logger
from crimereporter.news.commands.simple import SimpleCommand
from crimereporter.news.renderers.video import VideoRenderer


class VideoCommand(SimpleCommand):

    def run(self) -> None:
        filename = self.input_file.parent / "output" / f"{self.orientation}.mp4"
        if not self.should_run(filename):
            logger.info("Video already exists, skipping")
            return
        renderer = VideoRenderer()
        renderer.render(self.script, self.orientation, filename)
        if platform.system() == "Windows":
            os.startfile(filename)
        else:
            raise NotImplementedError
