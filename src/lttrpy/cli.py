#!/usr/bin/env python

# SPDX-License-Identifier: MIT
# MIT License
# Copyright (c) 2024 Said Sattarov
# See https://mit-license.org/ for the full text of the license


import asyncio
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Iterable

from aiohttp import ClientSession

from lttrpy import __version__
from lttrpy.letterboxd_profile import LetterboxdProfile
from lttrpy.output_formatter import Formatter


async def lttrpy() -> None:
    parser: ArgumentParser = ArgumentParser(description="Compare Letterboxd users' watched films")
    parser.add_argument(
        "-f",
        "--format",
        help="Output format (defaults to HTML)",
        default=["html"],
        nargs="+",
        dest="formats",
        choices=("md", "html"),
    )
    parser.add_argument(
        "users",
        metavar="user",
        nargs="+",
        help="Letterboxd username",
        type=str,
    )
    parser.add_argument("-o", "--output", dest="outfile", help="Output file", type=str)
    parser.add_argument(
        "-v",
        help="print current version and exit",
        action="version",
        version=__version__,
    )
    args: Namespace = parser.parse_args()

    async with ClientSession(raise_for_status=True) as client:
        create_profiles: tuple = tuple(
            LetterboxdProfile.initialise(user, client) for user in args.users
        )
        profiles: Iterable[LetterboxdProfile] = await asyncio.gather(*create_profiles)

    formatted_output: Formatter = Formatter(profiles)

    for form in args.formats:
        if args.outfile:
            filename: Path = Path(args.outfile)
        else:
            filename: Path = Path(
                f"{'_'.join(sorted([p.username for p in profiles]))}",
            ).with_suffix(f".{form}")

        formatted_output.write(filename, out_format=form)


def main() -> None:
    asyncio.run(lttrpy())
