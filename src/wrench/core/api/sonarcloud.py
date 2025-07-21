# pylint: disable=C0114,C0115,C0116
import asyncio
import enum
import typing as tp

import aiohttp
import aiohttp.web

from ...config.config import read_config

Params = dict[str, str]
ClientSession = aiohttp.ClientSession | None


def strip_none(d: dict) -> dict:
    return {k: v for k, v in d.items() if v is not None}


class Method(enum.StrEnum):
    GET_COMPONENTS_SEARCH = 'components/search'
    GET_MEASURES_COMPONENT = 'measures/component'


class APIBase:
    def __init__(self, *, token: str):
        self.token = token
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json',
        }

    @property
    def base_url(self) -> str:
        base_url = str(read_config('.env').get('SONAR_BASE_URL'))
        return base_url.strip('/')

    def url_for(self, method: Method, **kwargs) -> str:
        m = method.format(**kwargs)
        return f'{self.base_url}/{m}'

    async def _get(self, method: Method, params: Params) -> dict[str, tp.Any]:
        assert method is not None

        url = self.url_for(method)
        async with self._session.get(url, params=params) as response:
            if response.ok:
                r = await response.json()
                return r
            else:
                return {}

    async def __aenter__(self):
        self._session = aiohttp.ClientSession(
            headers=self.headers, loop=asyncio.get_event_loop()
        )

    async def __aexit__(self, *args):
        await self._session.close()


class API(APIBase):
    async def get_components_search(
        self,
        *,
        org: str,
        page: int = 1,
        page_size: int = 100,
        q: str | None = None,
        **kwargs,
    ) -> dict[str, tp.Any]:
        assert org

        method = Method.GET_COMPONENTS_SEARCH

        params = kwargs | {'organization': org, 'p': page, 'ps': page_size, 'q': q}
        r = await self._get(method, strip_none(params))
        return r

    async def get_all_components(
        self, *, org: str, q: str | None = None
    ) -> dict[str, tp.Any]:
        assert org

        components = []
        page_size = 500

        r = await self.get_components_search(org=org, page_size=page_size, q=q)
        total = int(r['paging']['total'])
        components = r['components']

        how_many, reminder = divmod(total, page_size)
        page_sizes = (how_many - 1) * [page_size] + [reminder]

        for i, p in enumerate(page_sizes, 2):
            r = await self.get_components_search(org=org, page=i, page_size=p, q=q)
            components.extend(r['components'])

        return {
            'paging': {'pageIndex': 1, 'pageSize': page_size, 'total': total},
            'components': components,
        }

    async def get_measures_component(
        self,
        *,
        component: str,
        branch: str | None = None,
        metric_keys: str | None = None,
        additional_fields: str | None = None,
        pull_request: str | None = None,
        **kwargs,
    ) -> dict[str, tp.Any]:
        assert component

        method = Method.GET_MEASURES_COMPONENT

        default_metric_keys = ','.join(
            [
                'ncloc',
                'complexity',
                'cognitive_complexity',
                'reliability_rating',
                'quality_gate_details',
                'bugs',
                'security_rating',
                'security_hotspots_reviewed',
                'sqale_debt_ratio',
                'coverage',
                'tests',
                'violations',
                'sqale_index',
            ]
        )

        params = kwargs | {
            'component': component,
            'branch': branch,
            'metricKeys': metric_keys if metric_keys else default_metric_keys,
            'additionalFields': additional_fields,
            'pullRequest': pull_request,
        }
        r = await self._get(method, strip_none(params))
        return r


def create_api(token: str) -> API:
    return API(token=token)
