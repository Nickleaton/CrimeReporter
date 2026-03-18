import argparse
import logging.config

from crimereporter.grabber.commands.atom import YoutubeAtomCommand
from crimereporter.grabber.commands.command import ComposedCommand
from crimereporter.grabber.commands.commit import CommitCommand
from crimereporter.grabber.commands.download import DownloadCommand
from crimereporter.grabber.commands.index import IndexCommand
from crimereporter.grabber.commands.refresh import RefreshCommand
from crimereporter.grabber.commands.regenerate import RegenerateCommand
from crimereporter.sources.source import Source
from crimereporter.utils.config import Config
from crimereporter.utils.location import server_location

# from crimereporter.sources.atom import YouTubeAtomSource

config = Config()
logging.config.dictConfig(config.logging.to_dict())
logger = logging.getLogger(__name__)


def get_parser() -> argparse.ArgumentParser:
    argument_parser = argparse.ArgumentParser(description="Generate crime site.")
    argument_parser.add_argument(
        "-o", "--overwrite", action="store_true", default=False, help="Overwrite existing files"
    )
    argument_parser.add_argument("-f", "--source", type=str, required=False, help="Which source to process")
    subparsers = argument_parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("commit", help="Run commit command")
    subparsers.add_parser("download", help="Run download command")
    subparsers.add_parser("refresh", help="Run refresh command")
    subparsers.add_parser("index", help="Run index command")
    subparsers.add_parser("regenerate", help="Run regenerate command to rebuild a copy of message cache.")
    subparsers.add_parser("grab", help="Run grab command")
    subparsers.add_parser("youtube", help="Download from youtube atom feeds")

    return argument_parser


def main():
    # YouTubeAtomSource.load_atom_sources()
    Source.load_sources()
    parser = get_parser()
    args = parser.parse_args()
    if args.source:
        sources = Source.instances[args.source]
    else:
        sources = list(Source.instances.values())

    if args.command == "commit":
        command = CommitCommand(r"D:\PycharmProjects\CrimeReportData")
    elif args.command == "download":
        command = ComposedCommand([DownloadCommand(args.overwrite, source) for source in sources])
    elif args.command == "refresh":
        command = ComposedCommand([RefreshCommand(args.overwrite, source) for source in sources])
    elif args.command == "index":
        command = IndexCommand()
    elif args.command == "regenerate":
        command = RegenerateCommand()
    elif args.command == "grab":
        command = ComposedCommand(
            [
                ComposedCommand([DownloadCommand(args.overwrite, source) for source in sources]),
                IndexCommand(),
                CommitCommand(r"D:\PycharmProjects\CrimeReportData")
            ]
        )
    elif args.command == "youtube":
        command = ComposedCommand([YoutubeAtomCommand(args.overwrite, source) for source in sources])
    else:
        parser.print_help()
        return

    command.execute()


if __name__ == "__main__":
    logger.info("Starting")
    try:
        location = server_location()
        if location is None:
            logger.warning(f'Server is not in the United Kingdom "{location}"')
    except Exception as e:
        logger.warning("Location check server is down")
        logger.warning(str(e))
        location = None
    main()
    logger.info("Done")
