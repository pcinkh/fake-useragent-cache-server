import asyncio
import logging

import aiohttp
import async_timeout

logger = logging.getLogger(__name__)


async def ping(url, timeout, *, loop):
    async with aiohttp.ClientSession(loop=loop) as session:
        with async_timeout.timeout(timeout, loop=loop):
            try:
                async with session.get(url) as response:
                    logger.debug(response.status)
            except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                logger.exception(exc)


async def heartbeat(url, timeout, delay, *, loop):
    while True:
        try:
            try:
                await ping(url, timeout, loop=loop)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.exception(exc)

            await asyncio.sleep(delay, loop=loop)
        except asyncio.CancelledError:
            break
