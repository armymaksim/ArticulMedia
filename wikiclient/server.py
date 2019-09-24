"""
Инициализация веб сервиса
"""
import asyncio
import sys

import aioredis
from aiohttp import web
from importlib.machinery import SourceFileLoader
from jinja2 import Environment, PackageLoader, select_autoescape

from wikiclient.views import search

env = Environment(
    loader=PackageLoader('wikiclient', 'templates'),
    autoescape=select_autoescape(['html', 'xml']),
    enable_async=True
)


def get_config():
    if len(sys.argv) > 1:
        config = SourceFileLoader("config", sys.argv[1]).load_module()
    else:
        # На крайняк попробуем так (дефолтное хранилище админов)
        config = SourceFileLoader(
            "config",
            '/usr/local/etc/wikiclient/config.py'
        ).load_module()
    if hasattr(config, 'redis'):
        return config.redis
    raise ValueError('Нет настроек подключения к БД')


async def shutdown(app):
    await app.redis.close()
    sys.exit(0)

async def init_app():
    """
        Инициализируем приложение
    :return:
    """
    app = web.Application()
    try:
        app.redis = await aioredis.create_redis_pool(get_config())
    except aioredis.ConnectionClosedError:
        raise Exception('DSN сконфигурирован неверно '
                        'или БД недоступна')
    app.router.add_route('POST', '/', search)
    app.jinja = env
    app.on_shutdown.append(shutdown)

    return app


loop = asyncio.get_event_loop()
app = loop.run_until_complete(init_app())


def run(port=8080):
    web.run_app(app, port=port, handle_signals=True)
