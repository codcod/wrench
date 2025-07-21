"""Backstage API client for interacting with Software Catalog."""

# pylint: disable=C0115,C0116
import asyncio
import enum
import logging
import typing as tp

import aiohttp
from multidict import MultiDict

from ...config.config import read_config

# from ...config.settings import get_settings

Params = dict[str, str] | None
ClientSession = aiohttp.ClientSession | None


class HTTPError(Exception):
    """HTTP request error exception."""

    pass


class Method(enum.StrEnum):
    """API endpoint methods for Backstage Software Catalog."""

    GET_ENTITIES_BY_QUERY = 'entities/by-query'
    GET_ENTITIES = 'entities'


class APIBase:
    """Base class for Backstage API client functionality."""

    def __init__(self):
        self.headers = {
            'Accept': 'application/json',
        }
        self._session: ClientSession = None

    @property
    def base_url(self) -> str:
        base_url = str(read_config('.env').get('BACKSTAGE_BASE_URL'))
        # base_url = get_settings().backstage.base_url
        return base_url.strip('/')

    def url_for(self, method: Method, params: Params) -> str:
        """Build API URL for given method and parameters."""
        m = method
        if params:
            m = method.format(**params)
        return f'{self.base_url}/{m}'

    async def _get(
        self, method: Method, params: Params, query_params: Params
    ) -> dict[str, tp.Any]:
        """Execute single GET request to API endpoint."""
        assert method is not None
        assert self._session is not None

        url = self.url_for(method, params)

        async with self._session.get(url, params=query_params) as response:
            if response.ok:
                r = await response.json()
                return r
            else:
                raise HTTPError(
                    f'Error calling API method: {url}, status: {response.status}'
                )

    async def _mget(
        self, method: Method, params: Params, query_params: MultiDict
    ) -> list[dict[str, tp.Any]]:
        """Execute paginated GET requests to API endpoint."""
        assert method is not None
        assert self._session is not None

        url = self.url_for(method, params)
        logging.debug('get url: %s (no cursor)', url)

        async with self._session.get(url, params=query_params) as response:
            if response.ok:
                r = await response.json()
            else:
                raise HTTPError(
                    f'Error calling API method: {url}, status: {response.status}'
                )

        # Handle different API response formats
        if isinstance(r, list):
            # API returns list directly (no pagination)
            return r
        elif isinstance(r, dict) and 'items' in r:
            # API returns paginated response with items
            entities = r['items']
            # total_items = r.get('totalItems')
            page_info = r.get('pageInfo', {})
            next_cursor = page_info.get('nextCursor', '') if page_info else ''
        else:
            raise HTTPError(
                f'Unexpected API response format: {type(r).__name__}. '
                f'Expected list or dict with "items" key. '
                f'Got keys: {list(r.keys()) if isinstance(r, dict) else "N/A"}'
            )

        while next_cursor:
            query_params['cursor'] = next_cursor
            logging.debug('query_params=%s', query_params)

            logging.debug('get url: %s (cursor: %s)', url, next_cursor)
            async with self._session.get(url, params=query_params) as response:
                if response.ok:
                    r = await response.json()
                else:
                    raise HTTPError(
                        f'Error calling API method: {url}, status: {response.status}'
                    )

            if not isinstance(r, dict) or 'items' not in r:
                raise HTTPError(
                    f'Unexpected pagination response format: {type(r).__name__}'
                )

            batch = r['items']
            entities.extend(batch)
            logging.debug('len(batch)=%s', len(batch))
            page_info = r.get('pageInfo', {})
            next_cursor = page_info.get('nextCursor', '') if page_info else ''

        logging.debug('len(entities)=%s', len(entities))

        return entities

    async def __aenter__(self):
        self._session = aiohttp.ClientSession(
            headers=self.headers, loop=asyncio.get_event_loop()
        )

    async def __aexit__(self, *args):
        if self._session:
            await self._session.close()


class API(APIBase):
    """Backstage Software Catalog API client."""

    async def get_entities_by_query(
        self, *, params: Params = None, query_params: MultiDict
    ) -> list[dict[str, tp.Any]]:  # Changed: should return list, not dict
        method = Method.GET_ENTITIES_BY_QUERY
        logging.debug('call: get_entities_by_query')

        try:
            r = await self._mget(method, params=params, query_params=query_params)
        except HTTPError:
            logging.debug(
                'Error calling %s with %s and query %s', method, params, query_params
            )
            r = []  # Changed: return empty list instead of dict
        return r

    async def get_entities(
        self, *, params: Params = None, query_params: MultiDict | None = None
    ) -> list[dict[str, tp.Any]]:
        method = Method.GET_ENTITIES
        logging.debug('call: get_entities')

        try:
            if query_params is None:
                query_params = MultiDict()
            r = await self._mget(method, params=params, query_params=query_params)
        except HTTPError:
            logging.debug(
                'Error calling %s with %s and query %s', method, params, query_params
            )
            r = []
        return r


def create_api() -> API:
    """Create a new Backstage API client instance."""
    return API()
