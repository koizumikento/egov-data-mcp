import asyncio
import json
import sys
from argparse import SUPPRESS, ArgumentParser
from collections.abc import Sequence
from datetime import date

import httpx

from .client import get_dataset, get_dataset_history, search_datasets, search_resources


def run_cli(argv: Sequence[str]) -> None:
    parser = ArgumentParser(prog="egov-data-mcp")
    commands = parser.add_subparsers(required=True)

    command = commands.add_parser(
        "search-datasets", help="Search datasets by keyword.", argument_default=SUPPRESS
    )
    command.add_argument("--query", required=True)
    command.add_argument("--organization", help="CKAN organization slug, e.g. org_0400.")
    command.add_argument("--format", dest="file_format", help="File format, e.g. PDF.")
    command.add_argument("--updated-since", type=date.fromisoformat, metavar="YYYY-MM-DD")
    command.add_argument("--updated-until", type=date.fromisoformat, metavar="YYYY-MM-DD")
    command.add_argument("--limit", type=int)
    command.add_argument("--offset", type=int)
    command.set_defaults(handler=search_datasets)

    command = commands.add_parser(
        "get-dataset", help="Get dataset metadata and resource URLs.", argument_default=SUPPRESS
    )
    command.add_argument("--dataset-id", required=True)
    command.add_argument("--limit", type=int)
    command.add_argument("--offset", type=int)
    command.set_defaults(handler=get_dataset)

    command = commands.add_parser(
        "search-resources", help="Search distribution files by name.", argument_default=SUPPRESS
    )
    command.add_argument("--query", required=True)
    command.add_argument("--limit", type=int)
    command.add_argument("--offset", type=int)
    command.set_defaults(handler=search_resources)

    command = commands.add_parser(
        "get-dataset-history", help="Get catalog update events.", argument_default=SUPPRESS
    )
    command.add_argument("--dataset-id", required=True)
    command.add_argument("--limit", type=int)
    command.add_argument("--offset", type=int)
    command.set_defaults(handler=get_dataset_history)

    arguments = vars(parser.parse_args(argv))
    handler = arguments.pop("handler")
    try:
        result = asyncio.run(handler(**arguments))
        payload = result
    except (ValueError, OSError, httpx.HTTPError) as exc:
        parser.exit(1, f"{parser.prog}: {exc}\n")
    sys.stdout.buffer.write((json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8"))
