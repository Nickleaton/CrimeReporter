from pathlib import Path

from crimereporter.news.commands.simple import SimpleCommand
from crimereporter.utils.image_combiner import ImageCombiner


class ComposeImagesCommand(SimpleCommand):

    @staticmethod
    def process(target: Path, horizontal: int, vertical: int, sources: list[Path]):
        """Combine files and save to the target path."""
        # Ensure output directory exists
        target.parent.mkdir(parents=True, exist_ok=True)

        # Create combiner
        combiner = ImageCombiner(
            image_paths=sources,
            layout=(horizontal, vertical),
        )

        # Combine and save
        combined = combiner.combine()
        combined.save(target)

    def run(self) -> None:
        if "Images" in self.script.parsed:
            for name, image in self.script.parsed["Images"].items():
                self.process(
                    self.script.directory / Path(image["Target"]),
                    image["Horizontal"],
                    image["Vertical"],
                    [self.script.directory / Path(p) for p in image["Sources"]],
                )
        return
