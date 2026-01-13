from datetime import datetime

from git import Repo

from crimereporter.grabber.commands.command import Command
from crimereporter.utils.config import Config

config = Config()


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
        subdir: str = config.downloads
        iso_time: str = datetime.now().isoformat(timespec="seconds")
        commit_message: str = f"Download {iso_time}"

        self.repo.git.add(subdir)

        if self.repo.index.diff("HEAD") or self.repo.untracked_files:
            self.repo.git.commit("-m", commit_message, "--no-verify")
