import asyncio
import json
import sys
from argparse import SUPPRESS, ArgumentParser
from collections.abc import Sequence

import httpx

from .client import get_dataset, search_datasets


def run_cli(argv: Sequence[str]) -> None:
    parser = ArgumentParser(prog="egov-data-mcp")
    commands = parser.add_subparsers(required=True)

    command = commands.add_parser(
        "search-datasets", help="Search datasets by keyword.", argument_default=SUPPRESS
    )
    command.add_argument("--query", required=True)
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

    arguments = vars(parser.parse_args(argv))
    handler = arguments.pop("handler")
    try:
        result = asyncio.run(handler(**arguments))
        payload = result
    except (ValueError, OSError, httpx.HTTPError) as exc:
        parser.exit(1, f"{parser.prog}: {exc}\n")
    sys.stdout.buffer.write((json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8"))
