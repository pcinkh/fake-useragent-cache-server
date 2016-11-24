from functools import partial

from views import browsers


def setup_routes(app, *, loop):
    app.router.add_get(
        '/browsers/{version}',
        partial(browsers, loop=loop),
        name='browsers',
    )
