#!/usr/bin/env python

import argparse
import asyncio
import io
import json
import logging
import socket

from concurrent.futures import ThreadPoolExecutor
from functools import partial
from urllib.error import URLError

import uvloop
from aiohttp import web
from fake_useragent.settings import __version__ as fake_version
from fake_useragent.utils import load as fake_get_data

from routes import setup_routes


def refresh_cache():
    with io.open(
        'app/data/cached-{version}.json'.format(
            version=fake_version,
        ),
        mode='w+',
        encoding='utf-8',
    ) as cache_data:
        try:
            print('Fetching data through fake-useragent...')

            data = json.dumps(fake_get_data())

        except (URLError, socket.error) as exc:
            print('Error while fetching:', exc)

        else:
            print('Data fetched.')

            if data:
                print('Writing data...')

                cache_data.write(data)


async def periodic(*, loop, executor):
    while True:
        try:
            loop.run_in_executor(
                executor,
                partial(refresh_cache),
            )

            delay = 60 * 60  # 1 hour

            print('Sleeping for 1 hour...')

            await asyncio.sleep(delay, loop=loop)

        except asyncio.CancelledError:
            break


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--host',
        dest='host',
        help='server host listening',
        type=str,
        required=False,
    )
    parser.add_argument(
        '--port',
        dest='port',
        help='server port',
        type=int,
        required=False,
    )

    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG)

    asyncio.set_event_loop(None)

    loop = uvloop.new_event_loop()

    app = web.Application(loop=loop)

    setup_routes(app, loop=loop)

    handler = app.make_handler()

    server = loop.create_server(
        handler,
        args.host or '0.0.0.0',
        args.port or 8111,
    )

    executor = ThreadPoolExecutor(max_workers=2)

    try:
        _background = loop.create_task(periodic(loop=loop, executor=executor))

        srv = loop.run_until_complete(server)

        loop.run_forever()

    except KeyboardInterrupt:
        _background.cancel()

        loop.run_until_complete(_background)

    finally:
        srv.close()

        loop.run_until_complete(srv.wait_closed())

        loop.run_until_complete(app.shutdown())

        loop.run_until_complete(handler.finish_connections(60.0))

        loop.run_until_complete(app.cleanup())

        loop.close()
