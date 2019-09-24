import asyncio
import json
from datetime import datetime
from functools import wraps

import aiohttp


class TimeProfiler():

    def __init__(self):
        self.total = 0
        self.count = 0
        self.requests = []

    @classmethod
    def time(cls, f):
        @wraps(f)
        async def wrapper(self, *args, **kwds):
            start = datetime.now()
            res = await f(self, *args, **kwds)
            delta = datetime.now() - start
            self.total += delta.microseconds / 1000
            self.requests.append([f.__name__, delta.microseconds / 1000])
            self.count += 1
            return res
        return wrapper


class Cache(TimeProfiler):

    def __init__(self, connection):
        super().__init__()
        self.redis = connection

    @TimeProfiler.time
    async def exists(self, keys):
        pipe = self.redis.pipeline()
        for i in keys:
            pipe.exists(i)
        return await pipe.execute()

    @TimeProfiler.time
    async def get(self, key):
        return json.loads(await self.redis.get(key))

    @TimeProfiler.time
    async def save_to_cache(self, key, data):
        await self.redis.setex(key, 86400, json.dumps(data))


class WikiApi(TimeProfiler):
    url = 'https://en.wikipedia.org/w/api.php'

    def __init__(self):
        super().__init__()


    async def __make_request(self, url, payload):
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=payload) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    return {}

    async def search(self, text):
        resp = await self.search_pages(text)
        revs = await asyncio.gather(
            *[self.get_page_revisions(str(x['pageid']))
              for x in resp]
        )
        for i, x in enumerate(revs):
            resp[i]['revisions'] = x

        return dict(s_text=text, pages=resp)

    @TimeProfiler.time
    async def search_pages(self, text):
        params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "continue": "-||",
            "utf8": 1,
            "srsearch": text,
            "srlimit": "5",
            "srprop": "size|wordcount|timestamp|snippet"
        }
        resp = await self.__make_request(self.url, params)
        resp = resp.get("query", {}).get("search", [])
        return resp

    @TimeProfiler.time
    async def get_page_revisions(self, ids):
        params = {
            "action": "query",
            "format": "json",
            "prop": "revisions",
            "pageids": ids,
            "rvprop": "ids|timestamp|user|comment",
            "rvslots": "main",
            "rvlimit": "10",
            "rvdir": "older"
        }
        resp = await self.__make_request(self.url, params)

        return resp.get('query', {}) \
            .get('pages', {}) \
            .get(str(ids), {}) \
            .get('revisions', [])


class WikiClient(object):
    """ Фасад
    """

    def __init__(self, connection):
        self.__cache = Cache(connection)
        self.__api = WikiApi()

    async def search(self, words):
        coros = []
        for_save = []
        for i, exists in enumerate(await self.__cache.exists(words)):
            if exists:
                coros.append(self.__cache.get(words[i]))
            else:
                coros.append(self.__api.search(words[i]))
                for_save.append(i)
        data = await asyncio.gather(*coros)

        await asyncio.gather(
            *[self.__cache.save_to_cache(words[i], data[i]) for i in for_save]
        )

        return self.create_response(data)

    def create_response(self, data):
        res = dict(
            cache_time=self.__cache.total,
            api_time=self.__api.total,
            cache_count=self.__cache.count,
            api_count=self.__api.count,
            cache_requests=self.__cache.requests,
            api_requests=self.__api.requests,
            results=data
        )
        # self.__cache.requests = []
        # self.__api.requests = []
        return res
