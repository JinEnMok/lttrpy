#!/usr/bin/env python3

# MIT License
# Copyright (c) 2024 Said Sattarov
# See https://mit-license.org/ for the full text of the license

import asyncio

from argparse import ArgumentParser
from pathlib import Path
from aiohttp import ClientSession

from .LetterboxdProfile import LetterboxdProfile
from .OutputFormatter import Formatter


try:
    import uvloop
except ImportError:
    pass
else:
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


async def lttrpy() -> None:
    parser = ArgumentParser(description="Compare Letterboxd users' watched films")
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
    args = parser.parse_args()

    async with ClientSession(raise_for_status=True) as client:
        create_profiles: tuple = tuple(
            LetterboxdProfile.initialise(user, client) for user in args.users
        )
        profiles = await asyncio.gather(*create_profiles)

    formatted_output = Formatter(profiles)

    for form in args.formats:
        if args.outfile:
            filename = Path(args.outfile)
        else:
            filename = Path(
                f"{'_'.join(sorted([p.username for p in profiles]))}"
            ).with_suffix(f".{form}")

        formatted_output.write(filename, out_format=form)


def main() -> None:
    asyncio.run(lttrpy())


if __name__ == "__main__":
    main()
