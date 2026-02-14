import logging
from datetime import datetime
from pathlib import Path

from git import Repo

from crimereporter.grabber.commands.command import Command
from crimereporter.utils.config import Config

config = Config()

logger = logging.getLogger(__name__)

class CommitCommand(Command):
    """Command to commit downloaded articles to version control."""

    def __init__(self, repo: str) -> None:
        """Initialize the CommitCommand."""
        super().__init__()
        self.repo: Repo = Repo(repo)

    def execute(self) -> None:
        """
        Execute the commit command.

        Stages and commits any new or modified files in the 'downloads'
        directory using Git, with a timestamped commit message.
        """
        super().execute()
        iso_time: str = datetime.now().isoformat(timespec="seconds")
        commit_message: str = f"Download {iso_time}"

        self.repo.git.add(["downloads", "programs"])

        if self.repo.is_dirty(untracked_files=True):
            logger.info(f"git commit -m {commit_message} --no-verify")
            self.repo.git.commit("-m", commit_message, "--no-verify")
        else:
            logger.info("No changes to commit")
