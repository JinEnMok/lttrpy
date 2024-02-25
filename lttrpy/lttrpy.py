#!/usr/bin/env python

# MIT License
# Copyright (c) 2024 Said Sattarov
# See https://mit-license.org/ for the full text of the license

# Inspired by Sena Bayram's script


import sys
import asyncio

if sys.platform in ("linux", "darwin"):
    try:
        import uvloop
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    except ImportError:
        print("uvloop library not found. It could provide some speedups.")


from aiohttp import ClientSession
from .LetterboxdProfile import LetterboxdProfile
from .OutputFormatter import write_markdown


assert (
    sys.version_info[0] >= 3 and sys.version_info[1] >= 9
), "This script requires Python 3.9 or newer to run. Exiting."


async def main() -> None:
    async with ClientSession(raise_for_status=True) as client:
        tasks = tuple(
            LetterboxdProfile.initialise(user, client) for user in set(sys.argv[1:])
        )
        profiles = await asyncio.gather(*tasks)

    write_markdown(profiles, f"{'_'.join([p.username for p in profiles])}.md")


if __name__ == "__main__":
    asyncio.run(main())
