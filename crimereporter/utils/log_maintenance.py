import logging
from pathlib import Path
from threading import Lock

from crimereporter.utils.config import Config
from crimereporter.utils.singleton import singleton

config = Config()


@singleton
class GlobalScriptLogger:
    """Singleton logger for scripts and GUI output, with truncation and raw append support."""

    def __init__(self):
        self.log_file = Path(config.log.launcher_log)
        self.min_lines = config.log.min_lines
        self.max_lines = config.log.max_lines
        self._append_lock = Lock()

        self._setup_logger()

    def _setup_logger(self):
        """Configure the logger and truncate the log if needed."""
        self.truncate_log_if_needed()

        self.logger = logging.getLogger("launcher.gui")
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False

        if not any(isinstance(h, logging.FileHandler) for h in self.logger.handlers):
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(self.log_file, encoding="utf-8")
            formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def truncate_log_if_needed(self):
        """Truncate the log file if it exceeds the configured number of lines."""
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.log_file.exists():
            return

        try:
            with self.log_file.open(encoding="utf-8") as f:
                lines = f.readlines()
            if len(lines) > self.min_lines:
                with self.log_file.open("w", encoding="utf-8") as f:
                    f.writelines(lines[-self.max_lines :])
        except OSError as e:
            print(f"Warning: Could not truncate {self.log_file}: {e}")

    def append(self, text: str):
        """Append raw text to the log file (thread-safe, no formatting)."""
        stripped = text.rstrip("\n")
        if not stripped:
            return

        with self._append_lock:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            try:
                with self.log_file.open("a", encoding="utf-8") as f:
                    f.write(stripped + "\n")
                    f.flush()
            except OSError as e:
                print(f"Warning: Could not write to {self.log_file}: {e}")

    def get_logger(self) -> logging.Logger:
        """Return the configured logging.Logger instance."""
        return self.logger
