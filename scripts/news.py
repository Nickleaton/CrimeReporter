import argparse
import logging.config
import sys
from pathlib import Path

from crimereporter.grabber.commands.atom import YoutubeAtomCommand
from crimereporter.news.commands.ai import AIDownloadCommand, AITextCommand
from crimereporter.news.commands.archive import ArchiveCommand
from crimereporter.news.commands.audio import AudioCommand
from crimereporter.news.commands.compose_images import ComposeImagesCommand
from crimereporter.news.commands.composed import ComposedCommand
from crimereporter.news.commands.html import HTMLCommand
from crimereporter.news.commands.openstory import OpenStoryCommand
from crimereporter.news.commands.post import BlueskyPostCommand, XPostCommand
from crimereporter.news.commands.template import TemplateCommand
from crimereporter.news.commands.text import TextCommand
from crimereporter.news.commands.thumbnail import ThumbnailCommand
from crimereporter.news.commands.touch import TouchCommand
from crimereporter.news.commands.validate import ValidateCommand, ValidationError
from crimereporter.news.commands.video import VideoCommand
from crimereporter.utils.config import Config
from crimereporter.utils.directories import Directories
from crimereporter.youtube.captions import UploadCaptionsYoutubeCommand
from crimereporter.youtube.composed import YoutubeComposedCommand
from crimereporter.youtube.metadata import UpdateVideoMetadataCommand
from crimereporter.youtube.playlist import UpdatePlaylistCommand
from crimereporter.youtube.thumbnail import UploadThumbnailYoutubeCommand
from crimereporter.youtube.upload_video import UploadVideoYoutubeCommand

sys.path.append(str(Path(__file__).resolve().parent.parent))
config = Config()

# Exit codes
EXIT_SUCCESS = 0
EXIT_INVALID_COMMAND = 1
EXIT_VALIDATION_ERROR = 2
EXIT_MISSING_FILE = 3
EXIT_PERMISSION_DENIED = 4
EXIT_RUNTIME_ERROR = 5

# Logging setup
Path(f"{Path(config.root)}/logs").mkdir(exist_ok=True)
config = Config()
logging.config.dictConfig(config.logging.to_dict())
logger = logging.getLogger(__name__)

COMMAND_MAP = {
    "text": TextCommand,
    "thumbnail": ThumbnailCommand,
    "audio": AudioCommand,
    "video": VideoCommand,
    "html": HTMLCommand,
    "touch": TouchCommand,
    "open": OpenStoryCommand,
    "validate": ValidateCommand,
    "compose_image": ComposeImagesCommand,
    "xpost": XPostCommand,
    "blueskypost": BlueskyPostCommand,
    "upload_youtube_video": UploadVideoYoutubeCommand,
    "upload_youtube_thumbnail": UploadThumbnailYoutubeCommand,
    "upload_youtube_captions": UploadCaptionsYoutubeCommand,
    "upload_youtube_metadata": UpdateVideoMetadataCommand,
    "youtube": YoutubeComposedCommand,
    "archive": ArchiveCommand,
    "template": TemplateCommand,
    "aidownload": AIDownloadCommand,
    "aitext": AITextCommand,
    "youtube_atom": YoutubeAtomCommand,
    "playlist": UpdatePlaylistCommand,
}


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate videos.")
    parser.add_argument(
        "command",
        choices=list(COMMAND_MAP.keys()),
        nargs="+",
        help="Action to perform: generate videos or upload them",
    )
    parser.add_argument(
        "-p",
        "--program",
        type=int,
        help="Index of program (defaults depend on command)",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=["reel", "landscape"],
        default="landscape",
        help="Video format",
    )
    parser.add_argument("-s", "--source", type=str, help="Source")
    parser.add_argument("-i", "--identifier", type=str, help="ID of the story")
    parser.add_argument(
        "-t",
        "--target",
        choices=["Youtube", "Rumble", "X"],
        help="Platform to upload the video",
    )
    return parser


def build_commands(args):
    """Construct the list of commands to execute based on CLI arguments."""
    if args.program in (None, 0):
        args.program = (
            Directories.get_oldest_active_program()
            if any(cmd.lower() == "archive" for cmd in args.command)
            else Directories.get_newest_active_program()
        )

    commands = []
    for cmd_name in args.command:
        command_class = COMMAND_MAP.get(cmd_name)
        if not command_class:
            return None

        if command_class is TemplateCommand:
            commands.append(TemplateCommand(Directories.get_next_program()))
        elif command_class is ArchiveCommand:
            commands.append(ArchiveCommand())
        elif command_class is AIDownloadCommand:
            commands.append(AIDownloadCommand(args.source, args.identifier, Directories.get_next_program()))
        elif command_class is AITextCommand:
            commands.append(AITextCommand(args.script))
        else:
            filename = Path(config.root) / f"programs/Active/{args.program:05d}/script.yaml"
            commands.append(command_class(filename, args.format))

    return commands


def run_command(command):
    """Execute a command and handle common operational errors gracefully."""
    try:
        command.execute()
        return EXIT_SUCCESS

    except ValidationError as e:
        logger.error(str(e))
        return EXIT_VALIDATION_ERROR

    except FileNotFoundError as e:
        msg = f"{e.filename or ''}: {e.strerror or e}"
        logger.error(msg)
        return EXIT_MISSING_FILE

    except PermissionError as e:
        msg = f"Permission denied: {e.filename}"
        logger.error(msg)
        return EXIT_PERMISSION_DENIED

    except (RuntimeError, ValueError) as e:
        msg = f"Error: {e}"
        logger.error(msg)
        return EXIT_RUNTIME_ERROR


def main():
    parser = get_parser()
    args = parser.parse_args()

    commands_to_execute = build_commands(args)
    if not commands_to_execute:
        parser.print_help()
        return EXIT_INVALID_COMMAND

    command = commands_to_execute[0] if len(commands_to_execute) == 1 else ComposedCommand(commands_to_execute)

    return run_command(command)


if __name__ == "__main__":
    logger.info("Starting")
    res = main()
    logger.info("Done")
    sys.exit(res)
