import json

import aiofiles
from aiohttp import web

async def browsers(request, *, loop):
    async def read_data(path):
        async with aiofiles.open(
                path,
                mode='rt',
                encoding='utf-8',
                loop=loop,
        ) as cached_data:
            return await cached_data.read()

    data = None

    try:
        path = 'app/data/cached-{version}.json'.format(
            version=request.match_info['version'],
        )

        data = await read_data(path)

        if not data:
            path = 'data/default-{version}.json'.format(
                version=request.match_info['version'],
            )

            data = await read_data(path)

    except FileNotFoundError:
        path = 'app/data/default-{version}.json'.format(
            version=request.match_info['version'],
        )

        data = await read_data(path)

    finally:
        if data:
            return web.json_response(
                data=json.loads(data),
            )
        else:
            raise web.HTTPNotFound(
                text='No data was found for version {version}'.format(
                    version=request.match_info['version'],
                )
            )
