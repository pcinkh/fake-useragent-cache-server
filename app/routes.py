def setup_routes(app, handler):
    app.router.add_get(
        '/browsers/{version}',
        handler.browsers,
        name='browsers',
    )
