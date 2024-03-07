#!/usr/bin/env python

# MIT License
# Copyright (c) 2024 Said Sattarov
# See https://mit-license.org/ for the full text of the license

# Inspired by Sena Bayram's script

import sys
import asyncio

from aiohttp import ClientSession
from LetterboxdProfile import LetterboxdProfile
from OutputFormatter import Formatter


if sys.platform in ("linux", "darwin"):
    try:
        import uvloop

        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    except ImportError:
        print("uvloop library not found. It could provide some speedups.")


async def main() -> None:
    async with ClientSession(raise_for_status=True) as client:
        create_profiles: tuple = tuple(
            LetterboxdProfile.initialise(user, client) for user in set(sys.argv[1:])
        )
        profiles = await asyncio.gather(*create_profiles)

    filename: str = f"{'_'.join(sorted([p.username for p in profiles]))}.md"
    Formatter(profiles).write(filename, out_format="md")


if __name__ == "__main__":
    asyncio.run(main())
