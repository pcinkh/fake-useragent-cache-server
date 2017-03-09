import io
import json
import os

from aiohttp import web


class Handler:
    def __init__(self, *, loop):
        self.loop = loop

        self.files = {}

    def lookup_files(self, path):
        for obj in os.listdir(path):
            _path = os.path.join(path, obj)

            if os.path.isfile(_path):
                name, _ = os.path.splitext(obj)

                with io.open(_path, mode='rt', encoding='utf-8') as fp:
                    self.files[name] = json.dumps(json.load(fp)).encode('utf-8')  # noqa

    def browsers(self, request):
        version = request.match_info['version']

        if version not in self.files:
            raise web.HTTPNotFound(
                text='No data was found for version {version}'.format(
                    version=version,
                ),
            )

        return web.json_response(body=self.files[version])
