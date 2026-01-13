import platform
import subprocess

from crimereporter.news.commands.commands import logger
from crimereporter.news.commands.simple import SimpleCommand


class OpenStoryCommand(SimpleCommand):

    def run(self) -> None:
        file_path = (self.input_file.parent / "output/story.html").resolve()
        if not self.should_run(file_path):
            logger.info("HTML already exists, skipping")
            return
        if platform.system() == "Windows":
            brave_path = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
            subprocess.run([brave_path, "--new-tab", str(file_path)])
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", "-a", "Brave Browser", str(file_path)])
        else:  # Linux
            subprocess.run(["brave-browser", "--new-tab", str(file_path)])
