from datetime import timedelta


class Timestamp:
    """Represents a start and end time for a segment."""

    def __init__(self, start: timedelta, end: timedelta):
        self.start = start
        self.end = end

    @staticmethod
    def ms_to_timedelta(ms: int) -> timedelta:
        """Convert milliseconds to a timedelta."""
        return timedelta(milliseconds=ms)

    @staticmethod
    def format(td: timedelta) -> str:
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        milliseconds = td.microseconds // 1000
        return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

    def __repr__(self):
        return f"{self.format(self.start)} --> {self.format(self.end)}"
