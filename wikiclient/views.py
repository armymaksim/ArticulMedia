from aiohttp.web_exceptions import HTTPBadRequest
from aiohttp.web_response import Response, json_response

from wikiclient.wikiclient import WikiClient


async def search(request):
    """
    Рендерит html код главной страницы
    :return: Response
    """
    data = await request.post()
    q = data.get('words')
    if q:
        words = q.split(';')
        results = await WikiClient(request.app.redis).search(words)
        return json_response(results)
    else:
        raise HTTPBadRequest(reason='Поле формы должно содержать текст')

