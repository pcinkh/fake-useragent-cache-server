#!/usr/bin/env python

import asyncio
import logging
import os
import signal
from functools import partial

import uvloop
from aiohttp import web
from fake_useragent import settings as fake_useragent_settings
from yarl import URL

from .routes import setup_routes
from .handlers import Handler
from .background import heartbeat

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def main():
    asyncio.set_event_loop(None)

    loop = uvloop.new_event_loop()

    handler = Handler(loop=loop)
    _root = os.path.abspath(os.path.dirname(__file__))
    handler.lookup_files(os.path.join(_root, 'data'))

    app = web.Application(
        debug=False,
        handler_factory=partial(
            web.RequestHandlerFactory,
            debug=False,
            keep_alive_on=False,
        ),
        loop=loop,
    )

    setup_routes(app, handler)

    handler = app.make_handler(access_log=None)

    server = loop.create_server(
        handler,
        os.environ.get('HOST', '0.0.0.0'),
        int(os.environ.get('PORT', 5000)),
    )

    url = URL(fake_useragent_settings.CACHE_SERVER).origin()

    _heartbeat = loop.create_task(heartbeat(url, 10, 60, loop=loop))

    srv = loop.run_until_complete(server)

    loop.add_signal_handler(signal.SIGINT, loop.stop)
    loop.add_signal_handler(signal.SIGTERM, loop.stop)
    loop.add_signal_handler(signal.SIGQUIT, loop.stop)

    try:
        loop.run_forever()

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
        loop.close()
