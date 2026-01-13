from crimereporter.news.commands.simple import SimpleCommand


class TouchCommand(SimpleCommand):

    def run(self) -> None:
        self.input_file.touch()
