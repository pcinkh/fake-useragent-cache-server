#!/usr/bin/env python
import asyncio
import os
import signal

import uvloop
from aiohttp import web
from yarl import URL

from .routes import setup_routes
from .handlers import Handler
from .background import heartbeat


def _sigint(signum, frame):
    os.kill(os.getpid(), signal.SIGINT)


def main():
    asyncio.set_event_loop(None)

    loop = uvloop.new_event_loop()

    handler = Handler(loop=loop)
    _root = os.path.abspath(os.path.dirname(__file__))
    handler.lookup_files(os.path.join(_root, 'data'))

    app = web.Application(loop=loop)

    setup_routes(app, handler)

    handler = app.make_handler(access_log=None)

    server = loop.create_server(
        handler,
        os.environ.get('HOST', '0.0.0.0'),
        int(os.environ.get('PORT', 5000)),
    )

    url = URL('https://fake-useragent.herokuapp.com/')

    _heartbeat = loop.create_task(heartbeat(url, 10, 60, loop=loop))

    srv = loop.run_until_complete(server)

    signal.signal(signal.SIGTERM, _sigint)

    try:
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass

        _heartbeat.cancel()

        try:
            loop.run_until_complete(_heartbeat)
        except asyncio.CancelledError:
            pass

        srv.close()

        loop.run_until_complete(srv.wait_closed())

        loop.run_until_complete(app.shutdown())

        loop.run_until_complete(handler.finish_connections(5.0))

        loop.run_until_complete(app.cleanup())

    finally:
        loop.call_soon(loop.stop)
        loop.run_forever()
        loop.close()
