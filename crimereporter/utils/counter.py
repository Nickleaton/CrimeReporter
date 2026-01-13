from pathlib import Path

from crimereporter.utils.singleton import singleton


@singleton
class Counter:
    def __init__(self, filename: str = "cache/counter.txt"):
        self.path = Path(filename)

    def next(self) -> int:
        if self.path.exists():
            text = self.path.read_text(encoding="utf-8").strip()
            try:
                count = int(text)
            except ValueError:
                count = 0
            count += 1
        else:
            count = 1

        self.path.write_text(str(count), encoding="utf-8")
        return count
