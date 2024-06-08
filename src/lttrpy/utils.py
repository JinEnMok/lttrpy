from asyncio import sleep
from functools import wraps
from typing import Awaitable, Callable

from aiohttp import ClientConnectionError


def retry(
    cooldown: int = 1,
    retries: int = 5,
) -> Callable:
    # http://allyouneedisbackend.com/blog/2017/09/15/how-backend-software-should-retry-on-failures/
    def wrap(func: Awaitable) -> Awaitable:
        @wraps(func)
        async def inner(
            *args,  # noqa: ANN002
            **kwargs,
        ):
            completed_tries: int = 0
            while completed_tries < retries:
                try:
                    return await func(*args, **kwargs)
                except (ClientConnectionError, TimeoutError) as e:
                    print(e)
                    await sleep(cooldown)
                    completed_tries += 1
                    continue
                else:
                    break
            return None
        return inner

    return wrap
