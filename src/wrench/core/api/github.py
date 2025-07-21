# pylint: disable=C0114,C0115,C0116
import asyncio
import enum
import logging
import typing as tp

import aiohttp

from ...config.config import read_config

Params = dict[str, str]
ClientSession = aiohttp.ClientSession | None


class HTTPError(Exception):
    pass


class Method(enum.StrEnum):
    GET_REPOSITORY_CONTENT = 'repos/{owner}/{repo}/contents/{path}'


class APIBase:
    def __init__(self, *, token: str):
        self.token = token
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/vnd.github+json',
        }

    @property
    def base_url(self) -> str:
        base_url = str(read_config('.env').get('GITHUB_BASE_URL'))
        return base_url.strip('/')

    def url_for(self, method: Method, params: Params) -> str:
        m = method.format(**params)
        return f'{self.base_url}/{m}'

    async def _get(self, method: Method, params: Params) -> dict[str, tp.Any]:
        assert method is not None

        url = self.url_for(method, params)

        async with self._session.get(url) as response:
            if response.ok:
                r = await response.json()
                return r
            else:
                raise HTTPError('Error calling API method: %s' % url)

    async def __aenter__(self):
        self._session = aiohttp.ClientSession(
            headers=self.headers, loop=asyncio.get_event_loop()
        )

    async def __aexit__(self, *args):
        await self._session.close()


class API(APIBase):
    async def get_repository_content(
        self,
        *,
        owner: str,
        repo: str,
        path: str,
    ) -> dict[str, tp.Any]:
        assert owner

        method = Method.GET_REPOSITORY_CONTENT

        params: Params = dict(owner=owner, repo=repo, path=path)
        try:
            logging.debug('calling method: %s with params: %s' % (method, params))
            r = await self._get(method, params=params)
        except HTTPError:
            logging.debug('Error calling {} with {}'.format(method, params))
            r = {}
        return r


def create_api(token: str) -> API:
    return API(token=token)
